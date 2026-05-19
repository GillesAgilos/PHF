from django import forms
from phf.utils import BaseEntityForm
from referential.models import AnalyticalMethod
from .models import Process, UnitOperation, Step, Parameter, Sample


class ProcessForm(BaseEntityForm):
    class Meta:
        model = Process
        fields = ['name', 'code', 'scale']


class UnitOperationForm(forms.ModelForm):
    class Meta:
        model = UnitOperation
        fields = ['name', 'unit_type', 'order']


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

class SampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        fields = ['sample_name', 'analytical_methods']
        widgets = {
            'sample_name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm border-secondary',
                'maxlength': '25',
                'required': True
            }),
            'analytical_methods': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrage et tri des méthodes analytiques actives pour le formulaire
        self.fields['analytical_methods'].queryset = AnalyticalMethod.objects.filter(
            is_active=True
        ).order_by('name')