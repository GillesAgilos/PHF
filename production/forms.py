from django import forms
from .models import Process, UnitOperation, Step, Parameter


class ProcessForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = ['code', 'scale']

class UnitOperationForm(forms.ModelForm):
    class Meta:
        model = UnitOperation
        fields = ['order', 'unit_type', 'name']

    def __init__(self, *args, **kwargs):
        self.process = kwargs.pop('process', None)
        super().__init__(*args, **kwargs)

    def clean_order(self):
        order = self.cleaned_data.get('order')
        if self.process and order:
            if UnitOperation.objects.filter(process=self.process, order=order).exists():
                raise forms.ValidationError(f"The position {order} is already occupied in this process.")
        return order

class StepForm(forms.ModelForm):
    class Meta:
        model = Step
        fields = ['name', 'order']

    def __init__(self, *args, **kwargs):
        self.unit_operation = kwargs.pop('unit_operation', None)
        super().__init__(*args, **kwargs)

    def clean_order(self):
        order = self.cleaned_data.get('order')
        if self.unit_operation and order:
            if Step.objects.filter(unit_operation=self.unit_operation, order=order, is_active=True).exists():
                raise forms.ValidationError(f"Step order {order} already exists for this unit.")
        return order

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

    def __init__(self, *args, **kwargs):
        self.step = kwargs.pop('step', None)
        super().__init__(*args, **kwargs)

    def clean_order(self):
        order = self.cleaned_data.get('order')
        if self.step and order:
            if Parameter.objects.filter(step=self.step, order=order, is_active=True).exists():
                raise forms.ValidationError(f"Order {order} already exists for this step.")
        return order