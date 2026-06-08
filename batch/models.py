from django.core.exceptions import ValidationError
from django.db import models
from phf.utils import BaseModel

class Batch(BaseModel):

    class CategoryChoices(models.TextChoices):
        MANUFACTURING = 'M-', 'Manufacturing'
        ENGINEERING = 'E-', 'Engineering'

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    project = models.ForeignKey(
        'referential.Project',
        on_delete=models.PROTECT,
        related_name='batches'
    )
    process = models.ForeignKey(
        'production.Process',
        on_delete=models.PROTECT,
        related_name='batches'
    )

    category = models.CharField(
        max_length=2,
        choices=CategoryChoices.choices,
        default=CategoryChoices.MANUFACTURING
    )
    iteration_number = models.PositiveIntegerField(
        default=1,
        verbose_name="Iteration number"
    )
    start_date = models.DateField(
        verbose_name="Start date",
        null=True,
        blank=True
    )
    end_date = models.DateField(
        verbose_name="End date",
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Batch"
        verbose_name_plural = "Batches"
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'process', 'iteration_number'],
                condition=models.Q(is_active=True),
                name='unique_active_iteration_per_project_process'
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
            expected_sample_count = 0

            for unit in active_units:
                active_steps = unit.steps.filter(is_active=True)
                for step in active_steps:
                    expected_param_count += step.parameters.filter(is_active=True).count()

                    for plan in step.sampling_plans.all():
                        expected_sample_count += plan.samples.filter(is_active=True).count()

            recorded_param_count = self.parameter_results.filter(is_active=True).count()
            recorded_sample_count = self.sample_results.filter(is_active=True).count()

            if recorded_param_count < expected_param_count:
                raise ValidationError(
                    f"Cannot validate batch: Missing parameter results. "
                    f"Recorded: {recorded_param_count}/{expected_param_count}."
                )

            if recorded_sample_count < expected_sample_count:
                raise ValidationError(
                    f"Cannot validate batch: Missing analytical sample results. "
                    f"Recorded: {recorded_sample_count}/{expected_sample_count}."
                )

    def save(self, *args, **kwargs):
        if self.is_active:
            self.full_clean()
        super().save(*args, **kwargs)



class ParameterResult(BaseModel):
    batch = models.ForeignKey(
        'batch.Batch',
        on_delete=models.CASCADE,
        related_name='parameter_results',
        verbose_name="Related Batch"
    )
    parameter = models.ForeignKey(
        'production.Parameter',
        on_delete=models.PROTECT,
        related_name='results',
        verbose_name="Process Parameter"
    )

    actual_value = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Actual Value"
    )
    comment = models.TextField(
        null=True,
        blank=True,
        verbose_name="Comment"
    )

    class Meta:
        verbose_name = "Parameter Result"
        verbose_name_plural = "Parameter Results"

    def clean(self):
        if self.batch and hasattr(self.batch, 'status') and self.batch.status == 'VALIDATED':
            raise ValidationError({
                'batch': "Batch is validated, no modification allowed."
            })

        if self.parameter:
            if hasattr(self.parameter, 'status') and self.parameter.status != 'VALIDATED':
                raise ValidationError({'parameter': f"Selected parameter ({self.parameter}) must be validated."})
            if hasattr(self.parameter, 'is_active') and not self.parameter.is_active:
                raise ValidationError({'parameter': f"Selected parameter ({self.parameter}) is archived."})

        if self.batch and not self.batch.is_active:
            raise ValidationError({'batch': "Cannot add or modify results on an archived batch."})

        if not self.actual_value and not self.comment:
            raise ValidationError({
                'comment': "A comment is required if no actual value is provided."
            })

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


class SampleResult(BaseModel):
    batch = models.ForeignKey(
        'batch.Batch',
        on_delete=models.CASCADE,
        related_name='sample_results',
        verbose_name="Related Batch"
    )
    sample = models.ForeignKey(
        'production.Sample',
        on_delete=models.PROTECT,
        related_name='results',
        verbose_name="Process Sample"
    )

    actual_value = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Actual Value"
    )
    comment = models.TextField(
        null=True,
        blank=True,
        verbose_name="Comment"
    )

    class Meta:
        verbose_name = "Sample Result"
        verbose_name_plural = "Sample Results"

    def clean(self):
        if self.batch and hasattr(self.batch, 'status') and self.batch.status == 'VALIDATED':
            raise ValidationError({
                'batch': "Batch is validated. No modification allowed."
            })

        if self.sample:
            if hasattr(self.sample, 'status') and self.sample.status != 'VALIDATED':
                raise ValidationError({'sample': f"Selected sample ({self.sample}) must be validated."})
            if hasattr(self.sample, 'is_active') and not self.sample.is_active:
                raise ValidationError({'sample': f"Selected sample ({self.sample}) is archived."})

        if self.batch and not self.batch.is_active:
            raise ValidationError({'batch': "Cannot add or modify results on an archived batch."})

        if not self.actual_value and not self.comment:
            raise ValidationError({
                'comment': "A comment is required if no actual value is provided."
            })

    def save(self, *args, **kwargs):
        if self.is_active:
            self.full_clean()
        models.Model.save(self, *args, **kwargs)

    def __str__(self):
        return f"{self.batch.name} - {self.sample.sample_name}: {self.actual_value or 'No Value'}"

    @property
    def edit_url(self):
        if self.status in ['VALIDATED']:
            return None
        return super().edit_url
