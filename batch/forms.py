from django import forms
from django.db.models import Max
from phf.utils import BaseEntityForm
from .models import Batch, ParameterResult, AnalysisResult
from referential.models import Project
from production.models import Process, Parameter, Analysis


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
            self.fields['process'].widget.attrs.update({'readonly': True, 'style': 'pointer-events: none; background-color: #e9ecef;'})
            self.fields['project'].widget.attrs.update({'readonly': True, 'style': 'pointer-events: none; background-color: #e9ecef;'})
            self.fields['category'].widget.attrs.update({'readonly': True, 'style': 'pointer-events: none; background-color: #e9ecef;'})

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
        self.fields['parameter'].queryset = Parameter.objects.filter(is_active=True)

        if self.instance and self.instance.pk:
            self.fields['batch'].widget.attrs.update({'readonly': True, 'style': 'pointer-events: none; background-color: #e9ecef;'})
            self.fields['parameter'].widget.attrs.update({'readonly': True, 'style': 'pointer-events: none; background-color: #e9ecef;'})

        target_parameter = None
        if self.instance and hasattr(self.instance, 'parameter') and self.instance.parameter:
            target_parameter = self.instance.parameter
        elif self.initial.get('parameter'):
            target_parameter = Parameter.objects.filter(pk=self.initial.get('parameter')).first()

        if target_parameter and getattr(target_parameter, 'format_type', None) == 'bool':
            self.fields['actual_value'].widget = forms.Select(
                choices=[('', '---------'), ('Yes', 'Yes'), ('No', 'No')],
                attrs={'class': 'form-select form-select-sm'}
            )


class AnalysisResultForm(BaseEntityForm):
    class Meta:
        model = AnalysisResult
        fields = ['batch', 'analysis', 'actual_value', 'comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['batch'].queryset = Batch.objects.filter(is_active=True)
        self.fields['analysis'].queryset = Analysis.objects.filter(is_active=True)

        if self.instance and self.instance.pk:
            self.fields['batch'].widget.attrs.update({'readonly': True, 'style': 'pointer-events: none; background-color: #e9ecef;'})
            self.fields['analysis'].widget.attrs.update({'readonly': True, 'style': 'pointer-events: none; background-color: #e9ecef;'})