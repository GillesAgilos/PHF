from django.db import models
from django.core.exceptions import PermissionDenied
from referential.models import BaseModel

# ==========================================
# METHODOLOGY MODELS
# ==========================================

class Process(BaseModel):
    name = models.CharField(max_length=255)
    scale = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_active:
            raise PermissionDenied("You are not authorized to modify archived processes.")
        return obj


class UnitOperation(BaseModel):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100) # e.g., USP, DSP

    def __str__(self):
        return f"{self.category} - {self.name}"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_active:
            raise PermissionDenied("You are not authorized to modify archived unit operations.")
        return obj


class ProcessStructure(BaseModel):
    """ Junction: Process <-> UnitOperation with Order """
    process = models.ForeignKey(Process, on_delete=models.CASCADE, related_name='structures')
    unit_operation = models.ForeignKey(UnitOperation, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']
        unique_together = ('process', 'order')

    def __str__(self):
        return f"{self.process.name} - Op {self.order}: {self.unit_operation.name}"


class Sequence(BaseModel):
    """ Sub-steps inside a Unit Operation """
    unit_operation = models.ForeignKey(UnitOperation, on_delete=models.CASCADE, related_name='sequences')
    name = models.CharField(max_length=255, verbose_name="Sequence Name")
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']
        unique_together = ('unit_operation', 'order')

    def __str__(self):
        return f"{self.unit_operation.name} > {self.name}"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_active:
            raise PermissionDenied("You are not authorized to modify archived sequences.")
        return obj


class Parameter(BaseModel):
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=50)
    range_values = models.CharField(max_length=255, help_text="NOR/PAR Ranges")

    def __str__(self):
        return f"{self.name} ({self.unit})"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_active:
            raise PermissionDenied("You are not authorized to modify archived parameters.")
        return obj


class Step(BaseModel):
    """ Junction: Sequence <-> Parameter with Target Value """
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE, related_name='steps')
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    instructed_value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.sequence.name} - {self.parameter.name}"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_active:
            raise PermissionDenied("You are not authorized to modify archived steps.")
        return obj