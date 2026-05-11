from django import forms
from .models import Batch, ParameterResult, SampleResult

class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = [
            'code', 'category', 'iteration_number',
            'project', 'process', 'sampling_plan',
            'start_date', 'end_date'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class ParameterResultForm(forms.ModelForm):
    class Meta:
        model = ParameterResult
        fields = ['batch', 'parameter', 'name', 'value', 'unit', 'format_type']

class SampleResultForm(forms.ModelForm):
    class Meta:
        model = SampleResult
        fields = ['batch', 'sample', 'name', 'value', 'unit', 'format_type']