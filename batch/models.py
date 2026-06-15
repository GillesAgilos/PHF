from django.core.exceptions import ValidationError
from django.db import models
from phf.utils import BaseModel


class Batch(BaseModel):
    class CategoryChoices(models.TextChoices):
        MANUFACTURING = 'M-', 'Manufacturing'
        ENGINEERING = 'E-', 'Engineering'

    name = models.CharField(max_length=100, unique=True)
    project = models.ForeignKey('referential.Project', on_delete=models.PROTECT, related_name='batches')
    process = models.ForeignKey('production.Process', on_delete=models.PROTECT, related_name='batches')
    category = models.CharField(max_length=2, choices=CategoryChoices.choices, default=CategoryChoices.MANUFACTURING)
    iteration_number = models.PositiveIntegerField(default=1, verbose_name="Iteration number")
    start_date = models.DateField(verbose_name="Start date", null=True, blank=True)
    end_date = models.DateField(verbose_name="End date", null=True, blank=True)

    class Meta:
        verbose_name = "Batch"
        verbose_name_plural = "Batches"
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'process', 'category', 'iteration_number'],
                condition=models.Q(is_active=True),
                name='unique_active_iteration_per_project_process_category'
            )
        ]

    def __str__(self):
        return f"{self.category} Lot (Iter: {self.iteration_number})"

    @property
    def edit_url(self):
        if self.status in ['VALIDATED']:
            return None
        return super().edit_url

    def clean(self):
        super().clean()

        if hasattr(self, 'status') and self.status == 'VALIDATED':
            process = self.process
            if not process:
                raise ValidationError("Cannot validate batch: No associated process found.")

            from production.models import UnitOperation

            active_units = UnitOperation.objects.filter(process=process, is_active=True)
            expected_param_count = 0
            expected_analysis_count = 0

            for unit in active_units:
                active_steps = unit.steps.filter(is_active=True)
                for step in active_steps:
                    expected_param_count += step.parameters.filter(is_active=True).count()
                    for sample in step.samples.all():
                        for analysis in sample.analyses.all():
                            expected_analysis_count += 1

            recorded_param_count = self.parameter_results.filter(is_active=True).count()
            recorded_analysis_count = self.analysis_results.filter(is_active=True).count()

            if recorded_param_count < expected_param_count:
                raise ValidationError(
                    f"Cannot validate batch: Missing parameter results. "
                    f"Recorded: {recorded_param_count}/{expected_param_count}."
                )

            if recorded_analysis_count < expected_analysis_count:
                raise ValidationError(
                    f"Cannot validate batch: Missing analytical results. "
                    f"Recorded: {recorded_analysis_count}/{expected_analysis_count}."
                )

    def save(self, *args, **kwargs):
        if self.is_active:
            self.full_clean()
        super().save(*args, **kwargs)


class ParameterResult(BaseModel):
    batch = models.ForeignKey('batch.Batch', on_delete=models.CASCADE, related_name='parameter_results',
                              verbose_name="Related Batch")
    parameter = models.ForeignKey('production.Parameter', on_delete=models.PROTECT, related_name='results',
                                  verbose_name="Process Parameter")
    actual_value = models.CharField(max_length=255, null=True, blank=True, verbose_name="Actual Value")
    comment = models.TextField(null=True, blank=True, verbose_name="Comment")

    class Meta:
        verbose_name = "Parameter Result"
        verbose_name_plural = "Parameter Results"

    def clean(self):
        models.Model.clean(self)

        if self.batch_id:
            if getattr(self.batch, 'status', None) == 'VALIDATED':
                raise ValidationError({'batch': "Batch is validated, no modification allowed."})
            if not self.batch.is_active:
                raise ValidationError({'batch': "Cannot add or modify results on an archived batch."})

        if self.parameter_id:
            if hasattr(self.parameter, 'is_active') and not self.parameter.is_active:
                raise ValidationError({'parameter': f"Selected parameter ({self.parameter}) is archived."})

        if not self.actual_value and not self.comment:
            raise ValidationError({'comment': "A comment is required if no actual value is provided."})

        if self.parameter_id and self.actual_value:
            if self.parameter.format_type == 'numeric':
                try:
                    val_float = float(self.actual_value.replace(',', '.'))
                except ValueError:
                    raise ValidationError({'actual_value': "The expected format for this parameter is numeric."})

                low = self.parameter.format_low_range
                high = self.parameter.format_high_range

                if low is not None and val_float < low:
                    raise ValidationError({'actual_value': f"Value {val_float} is below the allowed limit ({low})."})
                if high is not None and val_float > high:
                    raise ValidationError({'actual_value': f"Value {val_float} is above the allowed limit ({high})."})

            elif self.parameter.format_type == 'bool':
                if self.actual_value.strip().lower() not in ['yes', 'no', 'true', 'false', '1', '0', 'y', 'n', 'oui',
                                                             'non']:
                    raise ValidationError({'actual_value': "The expected format is a boolean choice (Yes/No)."})

    def save(self, *args, **kwargs):
        if self.is_active:
            self.full_clean()
        models.Model.save(self, *args, **kwargs)

    def __str__(self):
        return f"{self.batch.name} - {self.parameter.name}: {self.actual_value or 'No Value'}"

    @property
    def edit_url(self):
        if self.status in ['VALIDATED']:
            return None
        return super().edit_url


class AnalysisResult(BaseModel):
    batch = models.ForeignKey('batch.Batch', on_delete=models.CASCADE, related_name='analysis_results',
                              verbose_name="Related Batch")
    analysis = models.ForeignKey('production.Analysis', on_delete=models.PROTECT, related_name='results',
                                 verbose_name="Process Analysis")
    actual_value = models.CharField(max_length=255, null=True, blank=True, verbose_name="Actual Value")
    comment = models.TextField(null=True, blank=True, verbose_name="Comment")

    class Meta:
        verbose_name = "Analysis Result"
        verbose_name_plural = "Analysis Results"

    def clean(self):
        models.Model.clean(self)

        if self.batch_id:
            if getattr(self.batch, 'status', None) == 'VALIDATED':
                raise ValidationError({'batch': "Batch is validated. No modification allowed."})
            if not self.batch.is_active:
                raise ValidationError({'batch': "Cannot add or modify results on an archived batch."})

        if self.analysis_id:
            if hasattr(self.analysis, 'is_active') and not self.analysis.is_active:
                raise ValidationError({'analysis': f"Selected analysis ({self.analysis}) is archived."})

        if not self.actual_value and not self.comment:
            raise ValidationError({'comment': "A comment is required if no actual value is provided."})

        if self.analysis_id and self.actual_value:
            low = self.analysis.format_low_range
            high = self.analysis.format_high_range

            if low is not None or high is not None:
                try:
                    val_float = float(self.actual_value.replace(',', '.'))
                except ValueError:
                    raise ValidationError(
                        {'actual_value': "This analysis requires a numeric result to match its validation ranges."})

                if low is not None and val_float < low:
                    raise ValidationError(
                        {'actual_value': f"Value {val_float} is below the validation specifications ({low})."})
                if high is not None and val_float > high:
                    raise ValidationError(
                        {'actual_value': f"Value {val_float} is above the validation specifications ({high})."})

    def save(self, *args, **kwargs):
        if self.is_active:
            self.full_clean()
        models.Model.save(self, *args, **kwargs)

    def __str__(self):
        return f"{self.batch.name} - {self.analysis.analysis_name}: {self.actual_value or 'No Value'}"

    @property
    def edit_url(self):
        if self.status in ['VALIDATED']:
            return None
        return super().edit_url