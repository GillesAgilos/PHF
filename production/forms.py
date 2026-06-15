from django import forms
from django_select2.forms import Select2Widget
from phf.utils import BaseEntityForm
from referential.models import GlobalUnitOperation
from .models import Process, UnitOperation, Step, Parameter, Analysis, Sample


class ProcessForm(BaseEntityForm):
    class Meta:
        model = Process
        fields = ['name', 'code', 'scale']


class UnitOperationForm(forms.ModelForm):
    name = forms.ModelChoiceField(
        queryset=GlobalUnitOperation.objects.filter(status='VALIDATED', is_active=True),
        to_field_name='name',
        label="Unit Operation",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm border-secondary'}),
    )

    class Meta:
        model = UnitOperation
        fields = ['name', 'order']


class StepForm(forms.ModelForm):
    class Meta:
        model = Step
        fields = ['name', 'order']


class ParameterForm(forms.ModelForm):
    class Meta:
        model = Parameter
        fields = [
            'name', 'unit', 'format_type',
            'format_low_range', 'format_high_range',
            'low_proven_acceptable_range', 'high_proven_acceptable_range',
            'low_normal_operating_range', 'high_normal_operating_range',
            'order'
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
    class Meta:
        model = Sample
        fields = ['name']


class AnalysisForm(forms.ModelForm):
    class Meta:
        model = Analysis
        fields = ['analysis_name', 'analytical_method', 'format_low_range', 'format_high_range']
        widgets = {
            'analytical_method': Select2Widget(attrs={
                'data-placeholder': 'Search an analytical method...',
                'data-theme': 'bootstrap-5',
                'class': 'django-select2-custom form-select-sm'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        low = cleaned_data.get('format_low_range')
        high = cleaned_data.get('format_high_range')

        if low is not None and high is None:
            self.add_error('format_high_range', "High validation limit is required when Low limit is provided.")
        if high is not None and low is None:
            self.add_error('format_low_range', "Low validation limit is required when High limit is provided.")

        if low is not None and high is not None and low > high:
            self.add_error('format_low_range', "Low limit cannot be higher than High limit.")

        return cleaned_data

