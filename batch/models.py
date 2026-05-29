from django.core.exceptions import ValidationError
from django.db import models
from phf.utils import BaseModel

class Batch(BaseModel):

    class CategoryChoices(models.TextChoices):
        MANUFACTURING = 'M-', 'Manufacturing'
        ENGINEERING = 'E-', 'Engineering'

    class BatchStatus(models.TextChoices):
        RUNNING = 'RUNNING', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

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
    batch_status = models.CharField(
        max_length=20,
        choices=BatchStatus.choices,
        default=BatchStatus.RUNNING
    )

    class Meta:
        verbose_name = "Batch"
        verbose_name_plural = "Batches"

    def __str__(self):
        return f"{self.category} Lot (Iter: {self.iteration_number})"

    @property
    def edit_url(self):
        if self.status in ['VALIDATED']:
            return None
        return super().edit_url



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
