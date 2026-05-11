from django.db import models
from referential.models import BaseModel, Project
from production.models import Process, Parameter
from sampling.models import SamplingPlan, Sample


class Batch(BaseModel):
    CATEGORY_CHOICES = [
        ('M-', 'Manufacturing (M-)'),
        ('E-', 'Engineering (E-)'),
    ]

    code = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=2, choices=CATEGORY_CHOICES)
    iteration_number = models.PositiveIntegerField(default=1)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name='batches')

    process = models.ForeignKey(
        Process,
        on_delete=models.SET_NULL,
        related_name='batches',
        null=True,
        blank=True
    )
    sampling_plan = models.ForeignKey(
        SamplingPlan,
        on_delete=models.SET_NULL,
        related_name='batches',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.code} ({self.project.code})"


class ParameterResult(BaseModel):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='parameter_results')
    parameter = models.ForeignKey(Parameter, on_delete=models.PROTECT)

    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    unit = models.CharField(max_length=50, blank=True, null=True)
    format_type = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.batch.code} - {self.name}"


class SampleResult(BaseModel):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='sample_results')
    sample = models.ForeignKey(Sample, on_delete=models.PROTECT)

    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    unit = models.CharField(max_length=50, blank=True, null=True)
    format_type = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.batch.code} - {self.name}"