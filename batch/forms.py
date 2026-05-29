from django import forms
from phf.utils import BaseEntityForm
from .models import Batch, ParameterResult, SampleResult
from referential.models import Project
from production.models import Process, Parameter, Sample


class BatchForm(BaseEntityForm):
    class Meta:
        model = Batch
        fields = ['name', 'project', 'process', 'category', 'iteration_number', 'start_date', 'end_date', 'batch_status']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(is_active=True, status='VALIDATED')
        self.fields['process'].queryset = Process.objects.filter(is_active=True, status='VALIDATED')

        if self.instance and self.instance.pk:
            self.fields['process'].disabled = True
            self.fields['process'].required = False
            self.fields['project'].disabled = True
            self.fields['project'].required = False


class ParameterResultForm(BaseEntityForm):
    class Meta:
        model = ParameterResult
        fields = ['batch', 'parameter', 'actual_value', 'comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['batch'].queryset = Batch.objects.filter(is_active=True)

        self.fields['parameter'].queryset = Parameter.objects.filter(
            is_active=True
        )


class SampleResultForm(BaseEntityForm):
    class Meta:
        model = SampleResult
        fields = ['batch', 'sample', 'actual_value', 'comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['batch'].queryset = Batch.objects.filter(is_active=True)

        self.fields['sample'].queryset = Sample.objects.filter(
            is_active=True
        )