from django.db import models
from phf.utils import BaseModel, BaseComponentEntity
from django.core.exceptions import ValidationError

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

    @property
    def edit_url(self):
        if self.status in ['VALIDATED']:
            return None
        return super().edit_url


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
    format_type = models.CharField(max_length=20, choices=FORMAT_TYPE_CHOICES, default='numeric')
    order = models.PositiveIntegerField()

    unit = models.CharField(max_length=50)

    format_low_range = models.FloatField(blank=True, null=True, verbose_name="Format Low Range")
    format_high_range = models.FloatField(blank=True, null=True, verbose_name="Format High Range")

    low_proven_acceptable_range = models.FloatField(blank=True, null=True)
    high_proven_acceptable_range = models.FloatField(blank=True, null=True)
    low_normal_operating_range = models.FloatField(blank=True, null=True)
    high_normal_operating_range = models.FloatField(blank=True, null=True)

    class Meta:
        ordering = ['order']
        unique_together = ('step', 'order')

    def get_parent_entity(self):
        return self.step

    def __str__(self):
        return f"{self.name} ({self.step.name})"

    def clean(self):
        super().clean()

        if self.format_type == 'numeric':
            errors = {}
            if self.format_low_range is None:
                errors['format_low_range'] = "This field is required when the format type is Numeric."
            if self.format_high_range is None:
                errors['format_high_range'] = "This field is required when the format type is Numeric."

            if self.format_low_range is not None and self.format_high_range is not None:
                if self.format_low_range > self.format_high_range:
                    errors['format_low_range'] = "Low range cannot be higher than High range."

            if errors:
                raise ValidationError(errors)

        else:
            self.format_low_range = None
            self.format_high_range = None
            self.low_proven_acceptable_range = None
            self.high_proven_acceptable_range = None
            self.low_normal_operating_range = None
            self.high_normal_operating_range = None

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Sample(BaseComponentEntity):
    step = models.ForeignKey(
        Step,
        on_delete=models.CASCADE,
        related_name='samples',
        verbose_name="Related Step"
    )
    name = models.CharField(max_length=255, verbose_name="Sample Name")

    class Meta:
        verbose_name = "Sample"
        ordering = ['name']

    def get_parent_entity(self):
        return self.step

    def __str__(self):
        return f"Sample '{self.name}' for {self.step.name}"


class Analysis(BaseComponentEntity):
    sample = models.ForeignKey(
        Sample,
        on_delete=models.CASCADE,
        related_name='analyses',
        verbose_name="Related Sample"
    )
    analysis_name = models.CharField(
        max_length=25,
        verbose_name="Analysis Name"
    )
    analytical_method = models.ForeignKey(
        'referential.AnalyticalMethod',
        on_delete=models.PROTECT,
        related_name='analyses',
        verbose_name="Analytical Method",
        limit_choices_to={'status': 'VALIDATED', 'is_active': True}
    )

    format_low_range = models.FloatField(blank=True, null=True, verbose_name="Validation Low Range")
    format_high_range = models.FloatField(blank=True, null=True, verbose_name="Validation High Range")

    class Meta:
        verbose_name = "Analysis"
        verbose_name_plural = "Analyses"
        unique_together = ('sample', 'analysis_name', 'analytical_method')

    def get_parent_entity(self):
        return self.sample

    def __str__(self):
        return f"{self.analysis_name} -> {self.analytical_method.name}"

    def clean(self):
        super().clean()
        errors = {}

        if self.format_low_range is not None and self.format_high_range is None:
            errors['format_high_range'] = "High range is required when Low range is provided."
        if self.format_high_range is not None and self.format_low_range is None:
            errors['format_low_range'] = "Low range is required when High range is provided."

        if self.format_low_range is not None and self.format_high_range is not None:
            if self.format_low_range > self.format_high_range:
                errors['format_low_range'] = "Low range cannot be higher than High range."

        if errors:
            raise ValidationError(errors)
