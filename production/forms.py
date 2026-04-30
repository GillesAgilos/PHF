from django import forms
from .models import Batch, SamplingPlan, Sample, SampleResult
from referential.models import Project, AnalyticalMethod
from methodology.models import Process, Step

class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['project', 'process', 'iteration_number', 'category', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(is_active=True)
        self.fields['process'].queryset = Process.objects.filter(is_active=True)

class SamplingPlanForm(forms.ModelForm):
    class Meta:
        model = SamplingPlan
        fields = ['batch', 'analytical_method', 'sample_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['batch'].queryset = Batch.objects.filter(is_active=True)
        self.fields['analytical_method'].queryset = AnalyticalMethod.objects.filter(is_active=True)

class SampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        fields = ['step', 'phase', 'sample_date']
        widgets = {
            'sample_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['step'].queryset = Step.objects.filter(is_active=True)

class SampleResultForm(forms.ModelForm):
    class Meta:
        model = SampleResult
        fields = ['sampling_plan', 'value', 'unit']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sampling_plan'].queryset = SamplingPlan.objects.filter(is_active=True)