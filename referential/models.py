from django.db import models
from phf.utils import BaseModel


class Client(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class MoleculeType(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Project(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    molecule_name = models.CharField(max_length=255)

    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='projects',
        # only show validated and active clients in list dropdowns
        limit_choices_to={'status': 'VALIDATED', 'is_active': True}
    )
    molecule_type = models.ForeignKey(
        MoleculeType,
        on_delete=models.PROTECT,
        related_name='projects',
        # only show validated and active clients in list dropdowns
        limit_choices_to={'status': 'VALIDATED', 'is_active': True}
    )

    class Meta:
        unique_together = ('client', 'name')

    def __str__(self):
        return f"{self.code} - {self.name}"


class AnalyticalMethod(BaseModel):
    name = models.CharField(max_length=255, unique=True, verbose_name="Method Name")
    unit = models.CharField(max_length=255, verbose_name="Unit")
    sop_code = models.CharField(max_length=255, verbose_name="SOP Code")
    sop_version = models.CharField(max_length=50, verbose_name="SOP Version")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class GlobalUnitOperation(BaseModel):
    TYPE_CHOICES = [
        ('USP', 'USP'),
        ('DSP', 'DSP'),
    ]
    name = models.CharField(max_length=255, unique=True, verbose_name="Unit Name")
    unit_type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Type")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_unit_type_display()})"