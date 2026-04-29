from django import forms
from .models import Client, Project

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'code']

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['client', 'name', 'code']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.filter(is_active=True)
