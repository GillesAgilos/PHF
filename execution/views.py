from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Batch, ParameterResult, SampleResult
from .forms import BatchForm, ParameterResultForm, SampleResultForm
from phf.utils import AuditTrailMixin

# --- CRUD BATCH ---
class BatchListView(ListView):
    model = Batch
    template_name = 'execution/batch_list.html'
    context_object_name = 'batches'

class BatchCreateView(AuditTrailMixin, CreateView):
    model = Batch
    form_class = BatchForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('execution:batch_list')

class BatchUpdateView(AuditTrailMixin, UpdateView):
    model = Batch
    form_class = BatchForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('execution:batch_list')

class BatchDeleteView(DeleteView):
    model = Batch
    template_name = 'generic/generic_confirm_delete.html'
    success_url = reverse_lazy('execution:batch_list')


# --- CRUD PARAMETER RESULT ---
class ParameterResultListView(ListView):
    model = ParameterResult
    template_name = 'execution/parameter_result_list.html'

class ParameterResultCreateView(AuditTrailMixin, CreateView):
    model = ParameterResult
    form_class = ParameterResultForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('execution:parameter_result_list')

class ParameterResultUpdateView(AuditTrailMixin, UpdateView):
    model = ParameterResult
    form_class = ParameterResultForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('execution:parameter_result_list')

class ParameterResultDeleteView(DeleteView):
    model = ParameterResult
    template_name = 'generic/generic_confirm_delete.html'
    success_url = reverse_lazy('execution:parameter_result_list')


# --- CRUD SAMPLE RESULT ---
class SampleResultListView(ListView):
    model = SampleResult
    template_name = 'execution/sample_result_list.html'

class SampleResultCreateView(AuditTrailMixin, CreateView):
    model = SampleResult
    form_class = SampleResultForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('execution:sample_result_list')

class SampleResultUpdateView(AuditTrailMixin, UpdateView):
    model = SampleResult
    form_class = SampleResultForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('execution:sample_result_list')

class SampleResultDeleteView(DeleteView):
    model = SampleResult
    template_name = 'generic/generic_confirm_delete.html'
    success_url = reverse_lazy('execution:sample_result_list')