from django import forms
from .models import Client, Project, MoleculeType

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'code']

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['client', 'name', 'code', 'molecule_type', 'molecule_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow selection of entities that are both active and validated
        self.fields['client'].queryset = Client.objects.filter(
            is_active=True,
            status=Client.Status.VALIDATED
        )
        self.fields['molecule_type'].queryset = MoleculeType.objects.filter(
            is_active=True,
            status=MoleculeType.Status.VALIDATED
        )

class MoleculeTypeForm(forms.ModelForm):
    class Meta:
        model = MoleculeType
        fields = ['name', 'description']