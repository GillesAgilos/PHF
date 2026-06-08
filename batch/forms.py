from django import forms
from django.db.models import Max

from phf.utils import BaseEntityForm
from .models import Batch, ParameterResult, SampleResult
from referential.models import Project
from production.models import Process, Parameter, Sample


class BatchForm(BaseEntityForm):
    class Meta:
        model = Batch
        fields = ['name', 'project', 'process', 'category', 'iteration_number', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
            'iteration_number': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(is_active=True, status='VALIDATED')
        self.fields['process'].queryset = Process.objects.filter(is_active=True, status='VALIDATED')

        if self.instance and self.instance._state.adding is False:
            self.fields['process'].disabled = True
            self.fields['project'].disabled = True
            self.fields['category'].disabled = True

        elif self.instance._state.adding:
            project_id = self.data.get('project') or self.initial.get('project')
            process_id = self.data.get('process') or self.initial.get('process')
            category = self.data.get('category') or self.initial.get('category')

            if project_id and process_id and category:
                max_iter = Batch.objects.filter(
                    project_id=project_id,
                    process_id=process_id,
                    category=category,
                    is_active=True
                ).aggregate(Max('iteration_number'))['iteration_number__max']

                self.fields['iteration_number'].initial = (max_iter or 0) + 1
            else:
                self.fields['iteration_number'].initial = 1

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get('project')
        process = cleaned_data.get('process')
        category = cleaned_data.get('category')
        iteration_number = cleaned_data.get('iteration_number')

        if self.instance._state.adding and project and process and category and iteration_number:
            duplicate_exists = Batch.objects.filter(
                project=project,
                process=process,
                category=category,
                iteration_number=iteration_number,
                is_active=True
            ).exists()

            if duplicate_exists:
                self.add_error('iteration_number',
                               f"The iteration number {iteration_number} already exists for this configuration.")

        return cleaned_data

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