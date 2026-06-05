from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from production.models import Process
from .models import Client, Project, MoleculeType, AnalyticalMethod, GlobalUnitOperation
from .forms import ClientForm, ProjectForm, MoleculeTypeForm, AnalyticalMethodForm, GlobalUnitOperationForm
from phf.utils import AuditTrailMixin, StatusResetMixin, GenericDeleteView, GenericRestoreView, EntityDetailView, \
    EntityValidateView, EntityRejectView, FilterStateMixin
from.security import ReferentialRoleRequiredMixin


# ==========================================
# MOLECULE TYPE VIEWS
# ==========================================
class MoleculeTypeListView(ReferentialRoleRequiredMixin, FilterStateMixin, ListView):
    model = MoleculeType
    template_name = 'referential/molecule_type_list.html'
    context_object_name = 'molecule_types'
    search_fields = ['name']

class MoleculeTypeCreateView(ReferentialRoleRequiredMixin, AuditTrailMixin, CreateView):
    model = MoleculeType
    form_class = MoleculeTypeForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:moleculetype_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add New Molecule Type"
        return context

class MoleculeTypeUpdateView(ReferentialRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    model = MoleculeType
    form_class = MoleculeTypeForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:moleculetype_list')

class MoleculeTypeDeleteView(ReferentialRoleRequiredMixin, GenericDeleteView):
    model = MoleculeType
    success_url = reverse_lazy('referential:moleculetype_list')

class MoleculeTypeRestoreView(ReferentialRoleRequiredMixin, GenericRestoreView):
    model = MoleculeType
    redirect_url = 'referential:moleculetype_list'

class MoleculeTypeDetailView(ReferentialRoleRequiredMixin, EntityDetailView):
    model = MoleculeType


class MoleculeTypeValidateView(ReferentialRoleRequiredMixin, EntityValidateView):
    model = MoleculeType
    redirect_url = 'referential:moleculetype_list'

class MoleculeTypeRejectView(ReferentialRoleRequiredMixin, EntityRejectView):
    model = MoleculeType
    redirect_url = 'referential:moleculetype_list'

# ==========================================
# CLIENT VIEWS
# ==========================================
class ClientListView(ReferentialRoleRequiredMixin, FilterStateMixin, ListView):
    model = Client
    template_name = 'referential/client_list.html'
    context_object_name = 'clients'
    search_fields = ['name', 'code']

class ClientCreateView(ReferentialRoleRequiredMixin, AuditTrailMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:client_list')

class ClientUpdateView(ReferentialRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:client_list')

class ClientDeleteView(ReferentialRoleRequiredMixin, GenericDeleteView):
    model = Client
    success_url = reverse_lazy('referential:client_list')


class ClientRestoreView(ReferentialRoleRequiredMixin, GenericRestoreView):
    model = Client
    redirect_url = 'referential:client_list'

class ClientDetailView(ReferentialRoleRequiredMixin, EntityDetailView):
    model = Client

class ClientValidateView(ReferentialRoleRequiredMixin, EntityValidateView):
    model = Client
    redirect_url = 'referential:client_list'

class ClientRejectView(ReferentialRoleRequiredMixin, EntityRejectView):
    model = Client
    redirect_url = 'referential:client_list'

# ==========================================
# PROJECT VIEWS
# ==========================================
class ProjectListView(ReferentialRoleRequiredMixin, FilterStateMixin, ListView):
    model = Project
    template_name = 'referential/project_list.html'
    context_object_name = 'projects'
    search_fields = ['name', 'code', 'client__name']

    def get_queryset(self):
        return super().get_queryset().select_related('client', 'molecule_type')


class ProjectCreateView(ReferentialRoleRequiredMixin, AuditTrailMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:project_list')

class ProjectUpdateView(ReferentialRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:project_list')

class ProjectDeleteView(ReferentialRoleRequiredMixin, GenericDeleteView):
    model = Project
    success_url = reverse_lazy('referential:project_list')

class ProjectRestoreView(ReferentialRoleRequiredMixin, GenericRestoreView):
    model = Project
    redirect_url = 'referential:project_list'

class ProjectDetailView(ReferentialRoleRequiredMixin, EntityDetailView):
    model = Project

class ProjectValidateView(ReferentialRoleRequiredMixin, EntityValidateView):
    model = Project
    redirect_url = 'referential:project_list'

class ProjectRejectView(ReferentialRoleRequiredMixin, EntityRejectView):
    model = Project
    redirect_url = 'referential:project_list'

# ==========================================
# ANALYTICAL METHOD VIEWS
# ==========================================
class AnalyticalMethodListView(ReferentialRoleRequiredMixin, FilterStateMixin, ListView):
    model = AnalyticalMethod
    template_name = 'referential/analytical_method_list.html'
    context_object_name = 'analytical_methods'
    search_fields = ['name']

class AnalyticalMethodCreateView(ReferentialRoleRequiredMixin, AuditTrailMixin, CreateView):
    model = AnalyticalMethod
    form_class = AnalyticalMethodForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:analyticalmethod_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add New Analytical Method"
        return context

class AnalyticalMethodUpdateView(ReferentialRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    model = AnalyticalMethod
    form_class = AnalyticalMethodForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:analyticalmethod_list')

class AnalyticalMethodDeleteView(ReferentialRoleRequiredMixin, GenericDeleteView):
    model = AnalyticalMethod
    success_url = reverse_lazy('referential:analyticalmethod_list')

class AnalyticalMethodRestoreView(ReferentialRoleRequiredMixin, GenericRestoreView):
    model = AnalyticalMethod
    redirect_url = 'referential:analyticalmethod_list'

class AnalyticalMethodDetailView(ReferentialRoleRequiredMixin, EntityDetailView):
    model = AnalyticalMethod

class AnalyticalMethodValidateView(ReferentialRoleRequiredMixin, EntityValidateView):
    model = AnalyticalMethod
    redirect_url = 'referential:analyticalmethod_list'

class AnalyticalMethodRejectView(ReferentialRoleRequiredMixin, EntityRejectView):
    model = AnalyticalMethod
    redirect_url = 'referential:analyticalmethod_list'


def get_catalog_process():
    process, created = Process.objects.get_or_create(
        code="GLOBAL_CATALOG",
        defaults={"name": "Global Unit Operation Catalog Repository", "status": "DRAFT"}
    )
    return process

# =========================================================================
# GLOBAL UNIT OPERATION VIEWS
# =========================================================================

class GlobalUnitOperationListView(ReferentialRoleRequiredMixin, FilterStateMixin, ListView):
    model = GlobalUnitOperation
    template_name = 'referential/global_unit_list.html'
    context_object_name = 'global_units'
    search_fields = ['name']


class GlobalUnitOperationCreateView(ReferentialRoleRequiredMixin, AuditTrailMixin, CreateView):
    model = GlobalUnitOperation
    form_class = GlobalUnitOperationForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:globalunitoperation_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add New Global Unit Operation"
        return context


class GlobalUnitOperationUpdateView(ReferentialRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    model = GlobalUnitOperation
    form_class = GlobalUnitOperationForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:globalunitoperation_list')


class GlobalUnitOperationDeleteView(ReferentialRoleRequiredMixin, GenericDeleteView):
    model = GlobalUnitOperation
    success_url = reverse_lazy('referential:globalunitoperation_list')


class GlobalUnitOperationRestoreView(ReferentialRoleRequiredMixin, GenericRestoreView):
    model = GlobalUnitOperation
    redirect_url = 'referential:globalunitoperation_list'


class GlobalUnitOperationDetailView(ReferentialRoleRequiredMixin, EntityDetailView):
    model = GlobalUnitOperation


class GlobalUnitOperationValidateView(ReferentialRoleRequiredMixin, EntityValidateView):
    model = GlobalUnitOperation
    redirect_url = 'referential:globalunitoperation_list'


class GlobalUnitOperationRejectView(ReferentialRoleRequiredMixin, EntityRejectView):
    model = GlobalUnitOperation
    redirect_url = 'referential:globalunitoperation_list'