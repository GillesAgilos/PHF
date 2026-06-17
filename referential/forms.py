from phf.utils import BaseEntityForm
from .models import Client, Project, MoleculeType, AnalyticalMethod, GlobalUnitOperation


class ClientForm(BaseEntityForm):
    """
    Form class used for representing and validating client data.

    This class provides a form for interacting with `Client` model instances,
    allowing users to input and validate data for `name` and `code` fields.
    It extends from `BaseEntityForm`, which handles common functionality
    for entity-related forms.

    Attributes:
        Meta (type): Inner class containing metadata options.
            model (type): The model class associated with this form (Client).
            fields (List[str]): List of model fields to include in the form
            ("name", "code").
    """
    class Meta:
        model = Client
        fields = ['name', 'code']

class ProjectForm(BaseEntityForm):
    """
    Form for managing Project entities.

    This class provides a form implementation for creating and editing projects. It
    limits the selection of related entities to those that are both active and
    validated, ensuring consistency and integrity of the data. This form interacts
    with the `Project` model and enforces specific constraints on the available
    choices for some fields.

    Attributes:
        Meta.model (Model): The model associated with this form, i.e., `Project`.
        Meta.fields (list): The fields included in this form: `client`, `name`,
            `code`, `molecule_type`, `molecule_name`.
    """
    class Meta:
        model = Project
        fields = ['client', 'name', 'code', 'molecule_type', 'molecule_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow selection of entities that are both active and validated
        self.fields['client'].queryset = Client.objects.filter(
            is_active=True,
            status=Client.Status.VALIDATED
        )
        self.fields['molecule_type'].queryset = MoleculeType.objects.filter(
            is_active=True,
            status=MoleculeType.Status.VALIDATED
        )

class MoleculeTypeForm(BaseEntityForm):
    """
    Represents a form for interacting with the MoleculeType model.

    This class provides a form interface for creating and editing instances
    of the MoleculeType model. It is typically used in scenarios where data
    for a molecule type needs to be collected or validated through a UI form.
    The fields included in this form are 'name' and 'description'.

    Attributes:
        Meta (Meta): Contains metadata for the form, including associated model
            class and the fields to display.
    """
    class Meta:
        model = MoleculeType
        fields = ['name', 'description']

class AnalyticalMethodForm(BaseEntityForm):
    """
    Form for managing analytical method data.

    This class is designed for handling and validating input data related to
    analytical methods, such as their names, units, and associated SOP information.
    It provides a structure for collecting and processing data for analytical
    method instances within the system.

    Attributes:
        Meta (type): A nested class that specifies metadata options for the form,
            including the model it is associated with and the fields to be included.
    """
    class Meta:
        model = AnalyticalMethod
        fields = ['name', 'unit', 'sop_code', 'sop_version']


class GlobalUnitOperationForm(BaseEntityForm):
    """
    Represents a form for creating or updating GlobalUnitOperation entities.

    This class is designed to provide a form interface for managing
    instances of the GlobalUnitOperation model. It includes specific
    fields required for user input and potential customization of global
    unit operations within the system.

    Attributes:
        Meta (type): Contains metadata about the form, such as the model
            being used and the fields included in the form.
    """
    class Meta:
        model = GlobalUnitOperation
        fields = ['name', 'unit_type']