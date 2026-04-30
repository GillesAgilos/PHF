from django.db import models
from django.core.exceptions import PermissionDenied
from referential.models import BaseModel, Project, AnalyticalMethod
from methodology.models import Process, Step

# ==========================================
# PRODUCTION MODELS
# ==========================================

class Batch(BaseModel):
    """
    Execution instance linking a Project and a Manufacturing Process.
    """
    CATEGORY_CHOICES = [
        ('M-', 'Manufacturing'),
        ('E-', 'Engineering'),
    ]

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name='batches')
    process = models.ForeignKey(Process, on_delete=models.PROTECT, related_name='batches')
    iteration_number = models.PositiveIntegerField(verbose_name="Batch Number")
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='M-')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Batches"
        unique_together = ('category', 'iteration_number')

    def __str__(self):
        return f"{self.category}{self.iteration_number} ({self.project.code})"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_active:
            raise PermissionDenied("You are not authorized to modify archived batches.")
        return obj


class SamplingPlan(BaseModel):
    """
    Planning of tests for a specific Batch.
    Bridge between Production and Analytical Methods.
    """
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='sampling_plans')
    analytical_method = models.ForeignKey(AnalyticalMethod, on_delete=models.PROTECT)
    sample_name = models.CharField(max_length=255, help_text="Name of the expected sample")

    def __str__(self):
        return f"Plan: {self.sample_name} [{self.batch}]"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_active:
            raise PermissionDenied("You are not authorized to modify archived sampling plans.")
        return obj


class Sample(BaseModel):
    """
    The physical sample taken from the field.
    Linked to a methodology 'Step' to track exactly WHEN it was collected.
    """
    step = models.ForeignKey(Step, on_delete=models.PROTECT, related_name='samples')
    phase = models.CharField(max_length=100, help_text="e.g., In-process, Final product")
    sample_date = models.DateTimeField()

    def __str__(self):
        return f"Sample {self.phase} - {self.sample_date.strftime('%Y-%m-%d')}"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_active:
            raise PermissionDenied("You are not authorized to modify archived samples.")
        return obj


class SampleResult(BaseModel):
    """
    Final analytical data entry.
    """
    sampling_plan = models.ForeignKey(SamplingPlan, on_delete=models.CASCADE, related_name='results')
    value = models.CharField(max_length=255, verbose_name="Measured Value")
    unit = models.CharField(max_length=50)

    def __str__(self):
        return f"Result: {self.value} {self.unit} ({self.sampling_plan.sample_name})"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_active:
            raise PermissionDenied("You are not authorized to modify archived results.")
        return obj