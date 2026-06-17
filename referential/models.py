from django.db import models
from phf.utils import BaseModel


class Client(BaseModel):
    """
    Represents a client entity with a unique code and name.

    The Client class is designed to store information related to a client entity,
    where each client is identified by a unique code. This class provides basic
    information such as the name of the client and the corresponding unique code.
    It includes methods for user-friendly string representation.

    Attributes:
        name (str): The name of the client.
        code (str): The unique identifier code for the client.
    """
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class MoleculeType(BaseModel):
    """
    Represents a type of molecule.

    This class defines the properties of a molecule's type, including its name and
    an optional description. It is used to categorize different types of molecules
    by their characteristics. The `name` attribute is unique, ensuring that each
    type of molecule is distinct.

    Attributes:
        name (str): The unique name of the molecule type, up to 100 characters long.
        description (str or None): An optional textual description of the molecule
            type. This field can be left blank or null.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Project(BaseModel):
    """
    Represents a project entity within the application.

    This class is used to manage data related to projects, including their
    associated client, molecule type, and other attributes. Projects
    are uniquely identified by their `code` and are associated with
    validated and active clients and molecule types.

    Attributes:
        name (str): The name of the project.
        code (str): The unique identifier for the project.
        molecule_name (str): The name of the molecule associated with the
            project.
        client (Client): The client associated with this project. Only
            validated and active clients with their related `status` and
            `is_active` attributes are selectable.
        molecule_type (MoleculeType): The molecule type associated with this
            project. Only validated and active molecule types with their
            related `status` and `is_active` attributes are selectable.
    """
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
    """
    Represents an analytical method used for a specific purpose.

    This class provides a model for storing information about various analytical
    methods, including their name, unit of measure, SOP (Standard Operating
    Procedure) code, and SOP version. It is designed to store metadata about
    methodologies used in analytical work.

    Attributes:
        name (str): The name of the analytical method.
        unit (str): The unit of measure associated with the analytical method.
        sop_code (str): The standard operating procedure (SOP) code linked to
            the method.
        sop_version (str): The version of the SOP relevant to the method.
    """
    name = models.CharField(max_length=255, unique=True, verbose_name="Method Name")
    unit = models.CharField(max_length=255, verbose_name="Unit")
    sop_code = models.CharField(max_length=255, verbose_name="SOP Code")
    sop_version = models.CharField(max_length=50, verbose_name="SOP Version")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class GlobalUnitOperation(BaseModel):
    """
    Represents a global unit operation in a system.

    This class serves as a representation of different unit operations with specific
    types, used in a broader operational context. The unit operations are categorized
    under predefined types and are uniquely identified by their names.

    Attributes:
        name (str): Unique name of the unit operation.
        unit_type (str): Type of the unit operation, choices are 'USP' or 'DSP'.
    """
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