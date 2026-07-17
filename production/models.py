from django.db import models
from phf.utils import BaseModel, BaseComponentEntity
from django.core.exceptions import ValidationError

class Process(BaseModel):
    """
    Representation of a Process entity in the system.

    The Process class defines the structure for storing and managing data related
    to a process, including its status, name, code, scale, version, and parent
    version. It also includes metadata such as unique constraints and ordering.

    Attributes:
        status (str): The current status of the process. Choices include 'DRAFT',
            'PENDING', 'VALIDATED', and 'REJECTED'. Defaults to 'DRAFT'.
        name (str): The name of the process. Maximum length is 255 characters.
        code (str): The unique code identifying the process. Maximum length is
            100 characters.
        scale (str, optional): Additional information describing the scale of the
            process. Can be left blank. Maximum length is 100 characters.
        version (int): The numerical version of the process. Defaults to 1.
        parent_version (Process or None): A reference to the parent version of
            this process. Can be null or blank. Ensures a relationship between
            different versions of the same process.
    """
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
    """
    Represents a unit operation within a process in a given system.

    A unit operation can belong to either Upstream Processing (USP) or
    Downstream Processing (DSP). It is associated with a specific process
    and has attributes that define its unique characteristics and order
    within the process.

    Attributes:
        process (Process): The process to which this unit operation is associated.
        name (str): The name of the unit operation.
        unit_type (str): The type of the unit operation, chosen from TYPE_CHOICES
            ('USP' for Upstream Processing, 'DSP' for Downstream Processing).
        order (int): The order of this unit operation within the associated process.
    """
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
    """
    Represents a single step within a unit operation in a process.

    This class is used to define and manage the steps that belong to a specific
    unit operation. Each step has an associated name, order, and is linked to
    a parent unit operation. The ordering of steps is defined at the database level,
    ensuring proper sequence within a unit operation. The class also provides
    methods to fetch the parent entity and return a string representation of the
    step.

    Attributes:
        unit_operation (ForeignKey): The unit operation to which this step belongs.
        name (CharField): The name of the step.
        order (PositiveIntegerField): The sequence order of the step within the
            parent unit operation, ensuring sequential execution.
    """
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
    """
    Represents a parameter belonging to a specific step in a process.

    This class is designed to handle the definition and validation of various
    types of parameters attached to a process step, such as numeric values,
    boolean values, or text commentary. It includes configuration options for
    ordering, ranges, and units.

    Attributes:
        FORMAT_TYPE_CHOICES (list of tuple): Choices for the type of format
            the parameter can have, such as 'numeric', 'text', or 'bool'.
        step (ForeignKey): Reference to the Step that this parameter is associated
            with.
        name (str): The name of the parameter.
        format_type (str): The type of format for the parameter. Can be one of
            the options defined in FORMAT_TYPE_CHOICES.
        order (int): The display order for this parameter relative to other
            parameters in the same step.
        unit (str): The unit of measurement for the parameter.
        format_lower_range (float or None): The minimum acceptable value for the
            parameter when the format is numeric.
        format_upper_range (float or None): The maximum acceptable value for the
            parameter when the format is numeric.
        lower_proven_acceptable_range (float or None): The smallest proven
            acceptable value for the parameter.
        upper_proven_acceptable_range (float or None): The largest proven
            acceptable value for the parameter.
        lower_normal_operating_range (float or None): The minimum value for the
            normal operating range of the parameter.
        upper_normal_operating_range (float or None): The maximum value for the
            normal operating range of the parameter.
    """
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

    format_lower_range = models.FloatField(blank=True, null=True, verbose_name="Allowed Measurement Lower Range")
    format_upper_range = models.FloatField(blank=True, null=True, verbose_name="Allowed Measurement Upper Range")

    lower_proven_acceptable_range = models.FloatField(blank=True, null=True)
    upper_proven_acceptable_range = models.FloatField(blank=True, null=True)
    lower_normal_operating_range = models.FloatField(blank=True, null=True)
    upper_normal_operating_range = models.FloatField(blank=True, null=True)

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
            if self.format_lower_range is None:
                errors['format_lower_range'] = "This field is required when the format type is Numeric."
            if self.format_upper_range is None:
                errors['format_upper_range'] = "This field is required when the format type is Numeric."

            if self.format_lower_range is not None and self.format_upper_range is not None:
                if self.format_lower_range > self.format_upper_range:
                    errors['format_lower_range'] = "Lower range cannot be higher than Upper range."

            if errors:
                raise ValidationError(errors)

        else:
            self.format_lower_range = None
            self.format_upper_range = None
            self.lower_proven_acceptable_range = None
            self.upper_proven_acceptable_range = None
            self.lower_normal_operating_range = None
            self.upper_normal_operating_range = None

    def save(self, *args, **kwargs):
        if self.is_active:
            self.full_clean()
        super().save(*args, **kwargs)

class Sample(BaseComponentEntity):
    """Represents a sample entity related to a specific step in the system.

    This class models a sample, which is associated with a specific step through
    a foreign key relationship. The purpose of this class is to manage and represent
    individual samples with their corresponding metadata. The samples are ordered
    by their names for consistent display and querying purposes.

    Attributes:
        step: ForeignKey to the Step model that represents the step to which the sample
            belongs. It defines a cascading delete behavior and allows reverse access
            by the related name 'samples'.
        name: CharField representing the name of the sample. It has a maximum length
            constraint of 255 characters.

    """
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
    """
    Represents an analysis entity that connects a sample with an analytical method.

    This class is used to store information about a specific analysis on a given sample, including the
    analysis name, associated analytical method, and optional validation ranges. It enforces certain
    validation rules for the format ranges and ensures the uniqueness of entries based on sample,
    analysis name, and analytical method.

    Attributes:
        sample (ForeignKey): The sample associated with this analysis.
            The foreign key relationship ensures that each analysis is linked to a specific sample.
        analysis_name (CharField): The name of the analysis with a maximum length of 25 characters.
        analytical_method (ForeignKey): The analytical method associated with this analysis.
            The foreign key relationship enforces that only validated and active analytical methods
            can be assigned.
        format_lower_range (FloatField): The lower bound of the validation range. Can be blank or null.
        format_upper_range (FloatField): The upper bound of the validation range. Can be blank or null.
    """
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

    format_lower_range = models.FloatField(blank=True, null=True, verbose_name="Allowed Measurement Lower Range")
    format_upper_range = models.FloatField(blank=True, null=True, verbose_name="Allowed Measurement Upper Range")


    lower_normal_operating_range = models.FloatField(blank=True, null=True)
    upper_normal_operating_range = models.FloatField(blank=True, null=True)

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

        if self.lower_normal_operating_range is not None and self.upper_normal_operating_range is None:
            errors[
                'upper_normal_operating_range'] = "Upper normal operating range is required when Lower normal operating range is provided."
        if self.upper_normal_operating_range is not None and self.lower_normal_operating_range is None:
            errors[
                'lower_normal_operating_range'] = "Lower normal operating range is required when Upper normal operating range is provided."

        if self.lower_normal_operating_range is not None and self.upper_normal_operating_range is not None:
            if self.lower_normal_operating_range > self.upper_normal_operating_range:
                errors[
                    'lower_normal_operating_range'] = "Lower normal operating range cannot be higher than Upper normal operating range."

        if self.format_lower_range is not None and self.format_upper_range is None:
            errors['format_upper_range'] = "Upper range is required when Lower range is provided."
        if self.format_upper_range is not None and self.format_lower_range is None:
            errors['format_lower_range'] = "Lower range is required when Upper range is provided."

        if self.format_lower_range is not None and self.format_upper_range is not None:
            if self.format_lower_range > self.format_upper_range:
                errors['format_lower_range'] = "Lower range cannot be higher than Upper range."

        if errors:
            raise ValidationError(errors)
