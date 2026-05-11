from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from .models import Client, Project, MoleculeType
from .forms import ClientForm, ProjectForm, MoleculeTypeForm
from phf.utils import AuditTrailMixin, StatusResetMixin, GenericDeleteView, GenericRestoreView, EntityDetailView, \
    EntityValidateView, EntityRejectView, FilterStateMixin


# ==========================================
# MOLECULE TYPE VIEWS
# ==========================================
class MoleculeTypeListView(FilterStateMixin, ListView):
    model = MoleculeType
    template_name = 'referential/molecule_type_list.html'
    context_object_name = 'molecule_types'

class MoleculeTypeCreateView(AuditTrailMixin, CreateView):
    model = MoleculeType
    form_class = MoleculeTypeForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:moleculetype_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add New Molecule Type"
        return context

class MoleculeTypeUpdateView(AuditTrailMixin, StatusResetMixin, UpdateView):
    model = MoleculeType
    form_class = MoleculeTypeForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:moleculetype_list')

class MoleculeTypeDeleteView(GenericDeleteView):
    model = MoleculeType
    success_url = reverse_lazy('referential:moleculetype_list')

class MoleculeTypeRestoreView(GenericRestoreView):
    model = MoleculeType
    redirect_url = 'referential:moleculetype_list'

class MoleculeTypeDetailView(EntityDetailView):
    model = MoleculeType

class MoleculeTypeValidateView(EntityValidateView):
    model = MoleculeType
    redirect_url = 'referential:moleculetype_list'

class MoleculeTypeRejectView(EntityRejectView):
    model = MoleculeType
    redirect_url = 'referential:moleculetype_list'

# ==========================================
# CLIENT VIEWS
# ==========================================
class ClientListView(FilterStateMixin, ListView):
    model = Client
    template_name = 'referential/client_list.html'
    context_object_name = 'clients'
    queryset = Client.objects.all().order_by('-is_active', 'status', 'name')

class ClientCreateView(AuditTrailMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:client_list')

class ClientUpdateView(AuditTrailMixin, StatusResetMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:client_list')

class ClientDeleteView(GenericDeleteView):
    model = Client
    success_url = reverse_lazy('referential:client_list')

class ClientRestoreView(GenericRestoreView):
    model = Client
    redirect_url = 'referential:client_list'

class ClientDetailView(EntityDetailView):
    model = Client

class ClientValidateView(EntityValidateView):
    model = Client
    redirect_url = 'referential:client_list'

class ClientRejectView(EntityRejectView):
    model = Client
    redirect_url = 'referential:client_list'

# ==========================================
# PROJECT VIEWS
# ==========================================
class ProjectListView(FilterStateMixin, ListView):
    model = Project
    template_name = 'referential/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related('client', 'molecule_type')

class ProjectCreateView(AuditTrailMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:project_list')

class ProjectUpdateView(AuditTrailMixin, StatusResetMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:project_list')

class ProjectDeleteView(GenericDeleteView):
    model = Project
    success_url = reverse_lazy('referential:project_list')

class ProjectRestoreView(GenericRestoreView):
    model = Project
    redirect_url = 'referential:project_list'

class ProjectDetailView(EntityDetailView):
    model = Project

class ProjectValidateView(EntityValidateView):
    model = Project
    redirect_url = 'referential:project_list'

class ProjectRejectView(EntityRejectView):
    model = Project
    redirect_url = 'referential:project_list'
