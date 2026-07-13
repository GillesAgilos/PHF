from django.core.exceptions import ValidationError
from django.db import models
from phf.utils import BaseModel


class Batch(BaseModel):
    """
    Represents a batch in a production or engineering context with its associated properties and validation constraints.

    The Batch class is utilized to model a grouping of processes and projects in either manufacturing or engineering
    contexts. It enforces unique constraints, provides validation mechanisms, and integrates attributes such as category,
    project designation, and iteration information. It ensures data integrity and supports operations like validation
    checks for specific production-related requirements.

    Attributes:
        name (str): A unique name identifying the batch.
        project (referential.Project): A foreign key linking to the associated project.
        process (production.Process): A foreign key linking to the associated production process.
        category (str): Defines the category of the batch and is restricted to predefined choices
            (e.g., 'Manufacturing', 'Engineering').
        iteration_number (int): Specifies the iteration number of the batch.
        start_date (Optional[datetime.date]): The start date of the batch; can be left blank.
        end_date (Optional[datetime.date]): The end date of the batch; can be left blank.

        Meta:
            verbose_name (str): Human-readable name for this model ("Batch").
            verbose_name_plural (str): Human-readable plural name for this model ("Batches").
            constraints (list): Contains model-level constraints such as ensuring unique combinations of
                project, process, category, and iteration for active batches.
    """

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
                fields=['project', 'iteration_number'],
                condition=models.Q(is_active=True),
                name='unique_active_iteration_per_project'
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

            active_param_results = self.parameter_results.filter(is_active=True, parameter__is_active=True)
            active_analysis_results = self.analysis_results.filter(is_active=True, analysis__is_active=True)

            for unit in active_units:
                active_steps = unit.steps.filter(is_active=True)
                for step in active_steps:
                    expected_param_count += step.parameters.filter(is_active=True).count()
                    for sample in step.samples.filter(is_active=True):
                        for analysis in sample.analyses.filter(is_active=True):
                            expected_analysis_count += 1

            recorded_param_count = active_param_results.count()
            recorded_analysis_count = active_analysis_results.count()

            rejected_param_count = active_param_results.filter(status='REJECTED').count()
            rejected_analysis_count = active_analysis_results.filter(status='REJECTED').count()

            if rejected_param_count:
                raise ValidationError(
                    f"Cannot validate batch: {rejected_param_count} parameter result(s) have been rejected."
                )

            if rejected_analysis_count:
                raise ValidationError(
                    f"Cannot validate batch: {rejected_analysis_count} analytical result(s) have been rejected."
                )

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
    """
    Represents the result of a parameter associated with a batch in a production process.

    Encapsulates data related to a parameter's result, including its actual value and any comments.
    Ensures data integrity through validation rules, such as permissible value ranges and parameter
    status checks. It is typically associated with a batch and a production parameter, enforcing
    constraints based on their states (e.g., whether they are archived or validated).

    Attributes:
        batch (models.ForeignKey): A reference to the related batch this parameter result belongs to.
        parameter (models.ForeignKey): A reference to the production parameter this result corresponds to.
        actual_value (str): The actual value of the parameter (could be a numeric or other expected type).
        comment (str): A comment or note associated with the parameter result.

    """
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
                    normalized_value = self.actual_value.replace(',', '.')
                    val_float = float(normalized_value)
                    self.actual_value = normalized_value
                except ValueError:
                    raise ValidationError({'actual_value': "The expected format for this parameter is numeric."})

                low = self.parameter.format_lower_range
                high = self.parameter.format_upper_range

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
    """
    Represents the results of a specific analysis within a batch process.

    This class is used to record and validate the results of an analysis process
    related to a specific batch. It ensures that results conform to validation ranges
    when applicable and restricts modifications under certain conditions such as
    when the batch is already validated or archived.

    Attributes:
        batch (ForeignKey): The batch to which the analysis result is associated.
        analysis (ForeignKey): The production analysis for which the result is recorded.
        actual_value (CharField): The recorded value of the analysis. Can be null or blank.
        comment (TextField): An optional comment provided alongside the analysis result.

    """
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
            low = self.analysis.format_lower_range
            high = self.analysis.format_upper_range

            if low is not None or high is not None:
                try:
                    normalized_value = self.actual_value.replace(',', '.')
                    val_float = float(normalized_value)
                    self.actual_value = normalized_value
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
