from django import forms
from django_select2.forms import Select2Widget
from phf.utils import BaseEntityForm
from referential.models import GlobalUnitOperation
from .models import Process, UnitOperation, Step, Parameter, Sample, SamplingPlan


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


class SamplingPlanForm(forms.ModelForm):
    class Meta:
        model = SamplingPlan
        fields = ['name']


class SampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        fields = ['sample_name', 'analytical_method']
        widgets = {
            'analytical_method': Select2Widget(attrs={
                'data-placeholder': 'Search an analytical method...',
                'data-theme': 'bootstrap-5',
                'class': 'django-select2-custom form-select-sm'
            }),
        }

