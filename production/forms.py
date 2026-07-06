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
            'format_low_range', 'format_high_range',
            'low_proven_acceptable_range', 'high_proven_acceptable_range',
            'low_normal_operating_range', 'high_normal_operating_range'
        ]
        widgets = {
            'format_type': forms.Select(attrs={'class': 'form-select form-select-sm border-secondary'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        format_type = cleaned_data.get('format_type')
        format_low_range = cleaned_data.get('format_low_range')
        format_high_range = cleaned_data.get('format_high_range')

        if format_type == 'numeric':
            if format_low_range is None:
                self.add_error('format_low_range', "This field is required for Numeric parameters.")
            if format_high_range is None:
                self.add_error('format_high_range', "This field is required for Numeric parameters.")

            if format_low_range is not None and format_high_range is not None:
                if format_low_range > format_high_range:
                    self.add_error('format_low_range', "Low limit cannot be higher than High limit.")
        else:
            cleaned_data['format_low_range'] = None
            cleaned_data['format_high_range'] = None
            cleaned_data['low_proven_acceptable_range'] = None
            cleaned_data['high_proven_acceptable_range'] = None
            cleaned_data['low_normal_operating_range'] = None
            cleaned_data['high_normal_operating_range'] = None

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
            `format_low_range`, and `format_high_range`.
        Meta.widgets (dict): Custom widget configurations for form fields, such as
            specifying a styled searchable dropdown for the `analytical_method`.
    """
    class Meta:
        model = Analysis
        fields = [
            'analysis_name',
            'analytical_method',
            'low_normal_operating_range',
            'high_normal_operating_range',
            'format_low_range',
            'format_high_range',
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
        normal_low = cleaned_data.get('low_normal_operating_range')
        normal_high = cleaned_data.get('high_normal_operating_range')
        low = cleaned_data.get('format_low_range')
        high = cleaned_data.get('format_high_range')

        if normal_low is not None and normal_high is None:
            self.add_error(
                'high_normal_operating_range',
                "High normal operating range is required when Low normal operating range is provided."
            )
        if normal_high is not None and normal_low is None:
            self.add_error(
                'low_normal_operating_range',
                "Low normal operating range is required when High normal operating range is provided."
            )

        if normal_low is not None and normal_high is not None and normal_low > normal_high:
            self.add_error(
                'low_normal_operating_range',
                "Low normal operating range cannot be higher than High normal operating range."
            )

        if low is not None and high is None:
            self.add_error('format_high_range', "High validation limit is required when Low limit is provided.")
        if high is not None and low is None:
            self.add_error('format_low_range', "Low validation limit is required when High limit is provided.")

        if low is not None and high is not None and low > high:
            self.add_error('format_low_range', "Low limit cannot be higher than High limit.")

        return cleaned_data

