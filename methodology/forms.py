from django import forms
from .models import Process, UnitOperation, ProcessStructure, Sequence, Parameter, Step

class ProcessForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = ['name', 'scale']

class UnitOperationForm(forms.ModelForm):
    class Meta:
        model = UnitOperation
        fields = ['name', 'category']

class ProcessStructureForm(forms.ModelForm):
    class Meta:
        model = ProcessStructure
        fields = ['process', 'unit_operation', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['process'].queryset = Process.objects.filter(is_active=True)
        self.fields['unit_operation'].queryset = UnitOperation.objects.filter(is_active=True)

class SequenceForm(forms.ModelForm):
    class Meta:
        model = Sequence
        fields = ['unit_operation', 'name', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit_operation'].queryset = UnitOperation.objects.filter(is_active=True)

class ParameterForm(forms.ModelForm):
    class Meta:
        model = Parameter
        fields = ['name', 'unit', 'range_values']

class StepForm(forms.ModelForm):
    class Meta:
        model = Step
        fields = ['sequence', 'parameter', 'instructed_value']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sequence'].queryset = Sequence.objects.filter(is_active=True)
        self.fields['parameter'].queryset = Parameter.objects.filter(is_active=True)