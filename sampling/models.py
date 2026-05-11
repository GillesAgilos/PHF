from django.db import models
from production.models import Process, Step, UnitOperation, BaseModel
from referential.models import Project

class AnalyticalMethod(BaseModel):
    name = models.CharField(max_length=255)
    volume_required = models.FloatField()
    storage_temp = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class SamplingPlan(BaseModel):
    name = models.CharField(max_length=255)
    analytical_method = models.ManyToManyField(AnalyticalMethod, related_name='plan')

    def __str__(self):
        return f"{self.name}"

class Sample(BaseModel):
    sample_plan = models.ForeignKey(SamplingPlan, on_delete=models.CASCADE, related_name='entries')
    step = models.ForeignKey(Step, on_delete=models.PROTECT, related_name='samples')
    sample_name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "Sampling plan entries"

    def __str__(self):
        return f"{self.sample_name} - {self.step.name}"