from django import forms
from .models import SamplingPlan, Sample, AnalyticalMethod
from production.models import Step


class AnalyticalMethodForm(forms.ModelForm):
    class Meta:
        model = AnalyticalMethod
        fields = ['name', 'volume_required', 'storage_temp']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'volume_required': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'storage_temp': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SamplingPlanForm(forms.ModelForm):
    class Meta:
        model = SamplingPlan
        fields = ['name', 'analytical_method']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'analytical_method': forms.CheckboxSelectMultiple(),
        }


class SampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        fields = ['step', 'sample_name']
        widgets = {
            'step': forms.Select(attrs={'class': 'form-select'}),
            'sample_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['step'].queryset = Step.objects.filter(
            is_active=True
        ).select_related('unit_operation').order_by('unit_operation__name', 'order')

        self.fields['step'].label_from_instance = self.label_for_step

    def label_for_step(self, obj):
        unit = obj.unit_operation.name if obj.unit_operation else "N/A"
        return f"{unit} > {obj.name}"