from django.db import models
from phf.utils import BaseModel, BaseComponentEntity


class Process(BaseModel):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PENDING = 'PENDING', 'To Validate'
        VALIDATED = 'VALIDATED', 'Validated'
        REJECTED = 'REJECTED', 'Needs Correction'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    name = models.CharField(max_length=255, verbose_name="Process Name")
    code = models.CharField(max_length=100, verbose_name="Process Code")
    scale = models.CharField(max_length=100, blank=True, verbose_name="Scale")

    version = models.PositiveIntegerField(default=1, verbose_name="Version")
    parent_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_versions'
    )

    class Meta:
        unique_together = ('code', 'version')
        ordering = ['code', '-version']

    def __str__(self):
        return f"{self.code} v{self.version} ({self.scale})"


class UnitOperation(BaseComponentEntity):
    TYPE_CHOICES = [
        ('USP', 'USP (Upstream Processing)'),
        ('DSP', 'DSP (Downstream Processing)'),
    ]
    process = models.ForeignKey(
        Process,
        on_delete=models.CASCADE,
        related_name='units',
        verbose_name="Related Process"
    )
    name = models.CharField(max_length=255, verbose_name="Unit Name")
    unit_type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Type")
    order = models.PositiveIntegerField(verbose_name="Order in Process")

    class Meta:
        ordering = ['order']
        unique_together = ('process', 'order')

    def get_parent_entity(self):
        return self.process

    def __str__(self):
        return f"{self.name} ({self.unit_type})"

    @property
    def edit_url(self):
        return None


class Step(BaseComponentEntity):
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

    def get_parent_entity(self):
        return self.unit_operation

    def __str__(self):
        return f"{self.unit_operation.name} -> {self.name} (#{self.order})"


class Parameter(BaseComponentEntity):
    FORMAT_TYPE_CHOICES = [
        ('numeric', 'Numeric'),
        ('text', 'Text/Comment'),
        ('bool', 'Yes/No'),
    ]

    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name='parameters')
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=50, blank=True, null=True)
    format_type = models.CharField(max_length=20, choices=FORMAT_TYPE_CHOICES, default='numeric')

    # Validation Ranges
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

    def get_parent_entity(self):
        return self.step

    def __str__(self):
        return f"{self.name} ({self.step.name})"

class SamplingPlan(BaseComponentEntity):
    step = models.ForeignKey(
        Step,
        on_delete=models.CASCADE,
        related_name='sampling_plans',
        verbose_name="Related Step"
    )
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Sampling Plan"

    def get_parent_entity(self):
        return self.step

    def __str__(self):
        return f"Sampling Plan for {self.step.name}"


class Sample(BaseComponentEntity):
    sampling_plan = models.ForeignKey(
        SamplingPlan,
        on_delete=models.CASCADE,
        related_name='samples',
        verbose_name="Related Sampling Plan"
    )
    sample_name = models.CharField(
        max_length=25,
        verbose_name="Sample Name"
    )
    analytical_method = models.ForeignKey(
        'referential.AnalyticalMethod',
        on_delete=models.PROTECT,
        related_name='samples',
        verbose_name="Analytical Method",
        limit_choices_to={'is_active': True}
    )

    class Meta:
        unique_together = ('sampling_plan', 'sample_name', 'analytical_method')

    def get_parent_entity(self):
        return self.sampling_plan

    def __str__(self):
        return f"{self.sample_name} -> {self.analytical_method.name}"

