from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Client, Project, AnalyticalMethod
from .forms import ClientForm, ProjectForm, AnalyticalMethodForm

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
        return redirect('referential:client_list')

# ==========================================
# PROJECT VIEWS
# ==========================================

class ProjectListView(ListView):
    model = Project
    template_name = 'referential/project_list.html'
    context_object_name = 'projects'
    queryset = Project.objects.all().select_related('client').order_by('-is_active', 'name')

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
        return redirect('referential:project_list')

# ==========================================
# ANALYTICAL METHOD VIEWS
# ==========================================

class AnalyticalMethodListView(ListView):
    model = AnalyticalMethod
    template_name = 'referential/method_list.html'
    context_object_name = 'methods'
    queryset = AnalyticalMethod.objects.all().order_by('-is_active', 'name')

class AnalyticalMethodCreateView(CreateView):
    model = AnalyticalMethod
    form_class = AnalyticalMethodForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:method_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add Analytical Method"
        context['success_url'] = self.success_url
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class AnalyticalMethodUpdateView(UpdateView):
    model = AnalyticalMethod
    form_class = AnalyticalMethodForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:method_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Edit Method: {self.object.name}"
        context['success_url'] = self.success_url
        return context

    def form_valid(self, form):
        current_obj = self.get_object()
        if not current_obj.is_active:
            messages.error(self.request, "Error: method is archived, modification impossible.")
            return redirect('referential:method_list')
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class AnalyticalMethodDeleteView(DeleteView):
    model = AnalyticalMethod
    template_name = 'generic/generic_confirm_delete.html'
    success_url = reverse_lazy('referential:method_list')

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.delete(user=self.request.user)
        return HttpResponseRedirect(success_url)

class AnalyticalMethodRestoreView(View):
    def post(self, request, pk):
        method = get_object_or_404(AnalyticalMethod, pk=pk)
        method.restore()
        return redirect('referential:method_list')