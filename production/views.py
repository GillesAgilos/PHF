from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from .models import Batch, SamplingPlan, Sample, SampleResult
from .forms import BatchForm, SamplingPlanForm, SampleForm, SampleResultForm

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
# BATCH VIEWS
# ==========================================

class BatchListView(ListView):
    model = Batch
    template_name = 'production/batch_list.html'
    context_object_name = 'batches'
    # Show active batches first, then by start date
    queryset = Batch.objects.all().order_by('-is_active', '-start_date')

class BatchDetailView(DetailView):
    model = Batch
    template_name = 'production/batch_detail.html'
    context_object_name = 'batch'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add related data to the view for a full summary
        context['sampling_plans'] = self.object.sampling_plans.all()
        return context

class BatchCreateView(AuditTrailMixin, CreateView):
    model = Batch
    form_class = BatchForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('production:batch_list')

# ==========================================
# SAMPLING & RESULTS VIEWS
# ==========================================

class SampleCreateView(AuditTrailMixin, CreateView):
    model = Sample
    form_class = SampleForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('production:batch_list')

class SampleResultCreateView(AuditTrailMixin, CreateView):
    model = SampleResult
    form_class = SampleResultForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('production:batch_list')

# ==========================================
# RESTORE VIEW
# ==========================================
class ProductionRestoreView(View):
    def post(self, request, model_nm, pk):
        model_map = {
            'batch': Batch,
            'plan': SamplingPlan,
            'sample': Sample,
        }
        model = model_map.get(model_nm)
        obj = get_object_or_404(model, pk=pk)
        obj.restore()
        return redirect(request.META.get('HTTP_REFERER', 'production:batch_list'))