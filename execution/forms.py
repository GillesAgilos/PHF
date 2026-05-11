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
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

class ParameterResultForm(forms.ModelForm):
    class Meta:
        model = ParameterResult
        fields = ['batch', 'parameter', 'name', 'value', 'unit', 'format_type']

class SampleResultForm(forms.ModelForm):
    class Meta:
        model = SampleResult
        fields = ['batch', 'sample', 'name', 'value', 'unit', 'format_type']