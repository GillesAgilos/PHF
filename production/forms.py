from django import forms
from django_select2.forms import Select2Widget
from phf.utils import BaseEntityForm
from referential.models import GlobalUnitOperation
from .models import Process, UnitOperation, Step, Parameter, Analysis, Sample


class ProcessForm(BaseEntityForm):
    """
    Represents a form for managing Process entities.

    This class is used to define the structure and validation logic for forms
    associated with the `Process` model. It specifies the model and fields that
    should be included in the form. The form ensures data integrity and is an
    essential part of handling user input related to the `Process` model.

    Attributes:
        Meta (type): Contains metadata for the form, including the associated
            model and the fields to be included in the form.
    """
    class Meta:
        model = Process
        fields = ['name', 'code', 'scale']


class UnitOperationForm(forms.ModelForm):
    """
    Represents a form for handling unit operations in the application.

    This form is used to manage and validate data associated with a unit operation. It
    leverages a model choice field to select only validated and active global unit operations.
    The form is built on top of the `ModelForm` provided by Django and is tied to the
    `UnitOperation` model.

    Attributes:
        name (ModelChoiceField): A dropdown field allowing the selection of a unit
            operation, filtered to include only validated and active operations.
    """
    name = forms.ModelChoiceField(
        queryset=GlobalUnitOperation.objects.filter(status='VALIDATED', is_active=True),
        to_field_name='name',
        label="Unit Operation",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm border-secondary'}),
    )

    class Meta:
        model = UnitOperation
        fields = ['name']


class StepForm(forms.ModelForm):
    """
    Form class for creating and modifying Step objects.

    This class represents a form for the Step model, allowing users to create
    or edit Step instances. It includes specific fields from the Step model to
    be displayed and managed via the form.

    Attributes:
        Meta (type): Inner Meta class to define the Step model and the fields
            ['name', 'order'] included in the form.
    """
    class Meta:
        model = Step
        fields = ['name']


class ParameterForm(forms.ModelForm):
    """
    ParameterForm class for creating and validating Parameter model instances.

    This form is designed to handle validation based on the format type of the
    Parameter model. It ensures that certain conditions are met, such as numeric
    parameters requiring valid low and high range values, while gracefully handling
    cleanup of irrelevant fields for non-numeric formats.

    Attributes:
        Meta (type): Contains metadata for the model form, including the model and
            fields definitions.
    """
    class Meta:
        model = Parameter
        fields = [
            'name', 'unit', 'format_type',
            'format_lower_range', 'format_upper_range',
            'lower_proven_acceptable_range', 'upper_proven_acceptable_range',
            'lower_normal_operating_range', 'upper_normal_operating_range'
        ]
        widgets = {
            'format_type': forms.Select(attrs={'class': 'form-select form-select-sm border-secondary'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        format_type = cleaned_data.get('format_type')
        format_lower_range = cleaned_data.get('format_lower_range')
        format_upper_range = cleaned_data.get('format_upper_range')

        if format_type == 'numeric':
            if format_lower_range is None:
                self.add_error('format_lower_range', "This field is required for Numeric parameters.")
            if format_upper_range is None:
                self.add_error('format_upper_range', "This field is required for Numeric parameters.")

            if format_lower_range is not None and format_upper_range is not None:
                if format_lower_range > format_upper_range:
                    self.add_error('format_lower_range', "Lower limit cannot be higher than Upper limit.")
        else:
            cleaned_data['format_lower_range'] = None
            cleaned_data['format_upper_range'] = None
            cleaned_data['lower_proven_acceptable_range'] = None
            cleaned_data['upper_proven_acceptable_range'] = None
            cleaned_data['lower_normal_operating_range'] = None
            cleaned_data['upper_normal_operating_range'] = None

        return cleaned_data


class SampleForm(forms.ModelForm):
    """
    Represents a form for the Sample model.

    This class defines a form that is bound to the Sample model and allows for
    creating or updating instances of this model through user input. It includes
    fields specified in the `fields` attribute.

    Attributes:
        Meta (ModelMeta): Contains metadata that links the form to the
            associated model and defines which fields are included.
    """
    class Meta:
        model = Sample
        fields = ['name']


class AnalysisForm(forms.ModelForm):
    """
    Form for performing analysis operations, built upon Django's ModelForm.

    This class provides a representation of the `Analysis` model's form, handling
    field validations and custom widget configurations for user-friendly input. The
    form enforces constraints to ensure the logical consistency of numeric ranges
    entered in the associated fields.

    Attributes:
        Meta.model (type): The model class that the form is associated with, which
            is `Analysis`.
        Meta.fields (list): The list of model fields to include in the form,
            specifically `analysis_name`, `analytical_method`,
            `format_lower_range`, and `format_upper_range`.
        Meta.widgets (dict): Custom widget configurations for form fields, such as
            specifying a styled searchable dropdown for the `analytical_method`.
    """
    class Meta:
        model = Analysis
        fields = [
            'analysis_name',
            'analytical_method',
            'lower_normal_operating_range',
            'upper_normal_operating_range',
            'format_lower_range',
            'format_upper_range',
        ]
        widgets = {
            'analytical_method': Select2Widget(attrs={
                'data-placeholder': 'Search an analytical method...',
                'data-theme': 'bootstrap-5',
                'class': 'django-select2-custom form-select-sm'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        normal_lower = cleaned_data.get('lower_normal_operating_range')
        normal_upper = cleaned_data.get('upper_normal_operating_range')
        lower = cleaned_data.get('format_lower_range')
        upper = cleaned_data.get('format_upper_range')

        if normal_lower is not None and normal_upper is None:
            self.add_error(
                'upper_normal_operating_range',
                "Upper normal operating range is required when Lower normal operating range is provided."
            )
        if normal_upper is not None and normal_lower is None:
            self.add_error(
                'lower_normal_operating_range',
                "Lower normal operating range is required when Upper normal operating range is provided."
            )

        if normal_lower is not None and normal_upper is not None and normal_lower > normal_upper:
            self.add_error(
                'lower_normal_operating_range',
                "Lower normal operating range cannot be higher than Upper normal operating range."
            )

        if lower is not None and upper is None:
            self.add_error('format_upper_range', "Upper validation limit is required when Lower limit is provided.")
        if upper is not None and lower is None:
            self.add_error('format_lower_range', "Lower validation limit is required when Upper limit is provided.")

        if lower is not None and upper is not None and lower > upper:
            self.add_error('format_lower_range', "Lower limit cannot be higher than Upper limit.")

        return cleaned_data

