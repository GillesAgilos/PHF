from django.db import models
from referential.models import BaseModel


class Process(BaseModel):
    name = models.CharField(max_length=255, verbose_name="Unit Name")
    code = models.CharField(max_length=100, unique=True, verbose_name="Process Code")
    scale = models.CharField(max_length=100, blank=True, verbose_name="Scale")

    def __str__(self):
        return f"{self.code} ({self.scale})"


class UnitOperation(BaseModel):
    TYPE_CHOICES = [
        ('USP', 'USP'),
        ('DSP', 'DSP'),
    ]
    process = models.ForeignKey(
        Process,
        on_delete=models.CASCADE,
        related_name='units',
        verbose_name="Related Process"
    )
    name = models.CharField(max_length=255, verbose_name="Unit Name")
    unit_type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    order = models.PositiveIntegerField(verbose_name="Order in Process")

    class Meta:
        ordering = ['order']
        unique_together = ('process', 'order')

    def __str__(self):
        return f"{self.name} ({self.unit_type})"

class Step(BaseModel):
    unit_operation = models.ForeignKey(
        UnitOperation,
        on_delete=models.CASCADE,
        related_name='steps'
    )
    name = models.CharField(max_length=255, verbose_name="Step Name")
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']
        unique_together = ('unit_operation', 'order')

    def __str__(self):
        return f"{self.unit_operation.name} - {self.name} ({self.order})"


class Parameter(BaseModel):
    FORMAT_TYPE_CHOICES = [
        ('numeric', 'Numeric'),
        ('text', 'Text/Comment'),
        ('bool', 'Yes/No'),
    ]

    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name='parameters')
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=50, blank=True, null=True)
    format_type = models.CharField(max_length=20, choices=FORMAT_TYPE_CHOICES, default='numeric')

    # Validation Ranges (Format)
    format_low_range = models.FloatField(blank=True, null=True)
    format_high_range = models.FloatField(blank=True, null=True)

    # Proven Acceptable Range (PAR)
    low_proven_acceptable_range = models.FloatField(blank=True, null=True)
    high_proven_acceptable_range = models.FloatField(blank=True, null=True)

    # Normal Operating Range (NOR)
    low_normal_operating_range = models.FloatField(blank=True, null=True)
    high_normal_operating_range = models.FloatField(blank=True, null=True)

    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']
        unique_together = ('step', 'order')

    def __str__(self):
        return f"{self.name} ({self.step.name})"