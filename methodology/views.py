from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView
from .models import Process, UnitOperation, Sequence, Parameter
from .forms import ProcessForm, UnitOperationForm, SequenceForm, ParameterForm

# ==========================================
# MIXIN FOR AUDIT TRAIL
# ==========================================
class AuditTrailMixin:
    def form_valid(self, form):
        if not self.object:
            form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

# ==========================================
# PROCESS VIEWS
# ==========================================

class ProcessListView(ListView):
    model = Process
    template_name = 'methodology/process_list.html'
    context_object_name = 'processes'
    queryset = Process.objects.all().order_by('-is_active', 'name')

class ProcessCreateView(AuditTrailMixin, CreateView):
    model = Process
    form_class = ProcessForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('methodology:process_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Create New Process"
        return context

class ProcessUpdateView(AuditTrailMixin, UpdateView):
    model = Process
    form_class = ProcessForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('methodology:process_list')

    def form_valid(self, form):
        if not self.get_object().is_active:
            messages.error(self.request, "Archived process cannot be modified.")
            return redirect('methodology:process_list')
        return super().form_valid(form)

# ==========================================
# UNIT OPERATION VIEWS
# ==========================================

class UnitOperationListView(ListView):
    model = UnitOperation
    template_name = 'methodology/unit_op_list.html'
    context_object_name = 'unit_ops'
    queryset = UnitOperation.objects.all().order_by('-is_active', 'category')

class UnitOperationCreateView(AuditTrailMixin, CreateView):
    model = UnitOperation
    form_class = UnitOperationForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('methodology:unit_op_list')

class UnitOperationUpdateView(AuditTrailMixin, UpdateView):
    model = UnitOperation
    form_class = UnitOperationForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('methodology:unit_op_list')

# ==========================================
# SEQUENCE VIEWS
# ==========================================

class SequenceListView(ListView):
    model = Sequence
    template_name = 'methodology/sequence_list.html'
    context_object_name = 'sequences'
    queryset = Sequence.objects.all().select_related('unit_operation').order_by('unit_operation', 'order')

class SequenceCreateView(AuditTrailMixin, CreateView):
    model = Sequence
    form_class = SequenceForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('methodology:sequence_list')

# ==========================================
# PARAMETER VIEWS
# ==========================================

class ParameterListView(ListView):
    model = Parameter
    template_name = 'methodology/parameter_list.html'
    context_object_name = 'parameters'
    queryset = Parameter.objects.all().order_by('name')

class ParameterCreateView(AuditTrailMixin, CreateView):
    model = Parameter
    form_class = ParameterForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('methodology:parameter_list')

# ==========================================
# SHARED RESTORE VIEW
# ==========================================
class MethodologyRestoreView(View):
    def post(self, request, model_nm, pk):
        model_map = {
            'process': Process,
            'unitop': UnitOperation,
            'sequence': Sequence,
            'parameter': Parameter,
        }
        model = model_map.get(model_nm)
        obj = get_object_or_404(model, pk=pk)
        obj.restore()
        return redirect(request.META.get('HTTP_REFERER', 'methodology:process_list'))