from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Client, Project, MoleculeType
from .forms import ClientForm, ProjectForm, MoleculeTypeForm

# ==========================================
# MOLECULE TYPE VIEWS
# ==========================================

class MoleculeTypeListView(ListView):
    model = MoleculeType
    template_name = 'referential/molecule_type_list.html'
    context_object_name = 'molecule_types'
    queryset = MoleculeType.objects.all().order_by('-is_active', 'name')

class MoleculeTypeCreateView(CreateView):
    model = MoleculeType
    form_class = MoleculeTypeForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:molecule_type_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add New Molecule Type"
        context['success_url'] = self.success_url
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class MoleculeTypeUpdateView(UpdateView):
    model = MoleculeType
    form_class = MoleculeTypeForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:molecule_type_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Edit Molecule Type: {self.object.name}"
        context['success_url'] = self.success_url
        return context

    def form_valid(self, form):
        current_obj = self.get_object()
        if not current_obj.is_active:
            messages.error(self.request, "Error: molecule type is archived, modification impossible.")
            return redirect('referential:molecule_type_list')
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class MoleculeTypeDeleteView(DeleteView):
    model = MoleculeType
    template_name = 'generic/generic_confirm_delete.html'
    success_url = reverse_lazy('referential:molecule_type_list')

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.delete(user=self.request.user)
        return HttpResponseRedirect(success_url)

class MoleculeTypeRestoreView(View):
    def post(self, request, pk):
        m_type = get_object_or_404(MoleculeType, pk=pk)
        m_type.restore()
        messages.success(request, f"Molecule Type '{m_type.name}' restored successfully.")
        return redirect('referential:molecule_type_list')

# ==========================================
# CLIENT VIEWS
# ==========================================

class ClientListView(ListView):
    model = Client
    template_name = 'referential/client_list.html'
    context_object_name = 'clients'
    queryset = Client.objects.all().order_by('-is_active', 'name')

class ClientCreateView(CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:client_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add New Client"
        context['success_url'] = self.success_url
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class ClientUpdateView(UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:client_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Edit Client: {self.object.name}"
        context['success_url'] = self.success_url
        return context

    def form_valid(self, form):
        current_obj = self.get_object()
        if not current_obj.is_active:
            messages.error(self.request, "Error: client is archived, modification impossible.")
            return redirect('referential:client_list')
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class ClientDeleteView(DeleteView):
    model = Client
    template_name = 'generic/generic_confirm_delete.html'
    success_url = reverse_lazy('referential:client_list')

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.delete(user=self.request.user)
        return HttpResponseRedirect(success_url)

class ClientRestoreView(View):
    def post(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        client.restore()
        messages.success(request, f"Client '{client.name}' restored successfully.")
        return redirect('referential:client_list')

# ==========================================
# PROJECT VIEWS
# ==========================================

class ProjectListView(ListView):
    model = Project
    template_name = 'referential/project_list.html'
    context_object_name = 'projects'
    # Inclusion de molecule_type pour optimiser les requêtes SQL
    queryset = Project.objects.all().select_related('client', 'molecule_type').order_by('-is_active', 'name')

class ProjectCreateView(CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:project_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Create New Project"
        context['success_url'] = self.success_url
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class ProjectUpdateView(UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:project_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Edit Project: {self.object.name}"
        context['success_url'] = self.success_url
        return context

    def form_valid(self, form):
        current_obj = self.get_object()
        if not current_obj.is_active:
            messages.error(self.request, "Error: project is archived, modification impossible.")
            return redirect('referential:project_list')
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class ProjectDeleteView(DeleteView):
    model = Project
    template_name = 'generic/generic_confirm_delete.html'
    success_url = reverse_lazy('referential:project_list')

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.delete(user=self.request.user)
        return HttpResponseRedirect(success_url)

class ProjectRestoreView(View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        project.restore()
        messages.success(request, f"Project '{project.name}' restored successfully.")
        return redirect('referential:project_list')