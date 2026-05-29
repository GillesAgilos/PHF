from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from phf.utils import (
    FilterStateMixin, AuditTrailMixin, StatusResetMixin,
    GenericDeleteView, GenericRestoreView, EntityDetailView,
    EntityValidateView, EntityRejectView
)
from .models import Batch, SampleResult, ParameterResult
from .forms import BatchForm, ParameterResultForm, SampleResultForm
from production.models import UnitOperation, Step


# ==========================================
# BATCH VIEWS
# ==========================================
class BatchListView(FilterStateMixin, ListView):
    model = Batch
    template_name = 'batch/batch_list.html'
    context_object_name = 'batches'
    search_fields = ['project__name', 'process__code', 'batch_status']

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('-created_at').select_related('project', 'process')


class BatchCreateView(AuditTrailMixin, CreateView):
    model = Batch
    form_class = BatchForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('batch:batch_list')


class BatchUpdateView(AuditTrailMixin, StatusResetMixin, UpdateView):
    model = Batch
    form_class = BatchForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('batch:batch_list')


class BatchDeleteView(GenericDeleteView):
    model = Batch
    success_url = reverse_lazy('batch:batch_list')


class BatchRestoreView(GenericRestoreView):
    model = Batch
    redirect_url = 'batch:batch_list'


class BatchDetailView(EntityDetailView):
    model = Batch


class BatchValidateView(EntityValidateView):
    model = Batch
    redirect_url = 'batch:batch_list'


class BatchRejectView(EntityRejectView):
    model = Batch
    redirect_url = 'batch:batch_list'


class BatchLogbookView(DetailView):
    model = Batch
    template_name = 'batch/batch_logbook.html'
    context_object_name = 'batch'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batch = self.object
        process = batch.process

        units = UnitOperation.objects.filter(process=process, is_active=True).order_by('order')
        steps = Step.objects.filter(unit_operation__in=units, is_active=True).order_by('order').prefetch_related(
            'parameters', 'sampling_plans__samples__analytical_method'
        )

        param_results = {res.parameter_id: res for res in ParameterResult.objects.filter(batch=batch, is_active=True)}
        sample_results = {res.sample_id: res for res in SampleResult.objects.filter(batch=batch, is_active=True)}

        process_tree = []
        for unit in units:
            unit_data = {'object': unit, 'steps': []}
            unit_steps = [s for s in steps if s.unit_operation_id == unit.pk]
            for step in unit_steps:
                step_data = {'object': step, 'parameters_with_results': [], 'samples_with_results': []}

                for param in step.parameters.all():
                    step_data['parameters_with_results'].append({
                        'parameter': param,
                        'result': param_results.get(param.pk)
                    })

                for plan in step.sampling_plans.all():
                    for sample in plan.samples.all():
                        step_data['samples_with_results'].append({
                            'sample': sample,
                            'result': sample_results.get(sample.pk)
                        })
                unit_data['steps'].append(step_data)
            process_tree.append(unit_data)

        context['process_tree'] = process_tree
        return context


# ==========================================
# PARAMETER RESULT VIEWS
# ==========================================
class ParameterResultListView(FilterStateMixin, ListView):
    model = ParameterResult
    template_name = 'batch/parameter_result_list.html'
    context_object_name = 'parameter_results'
    search_fields = ['batch__name', 'parameter__name', 'actual_value']

    def get_queryset(self):
        queryset = ListView.get_queryset(self)
        search_query = self.request.GET.get('q')
        if search_query:
            from django.db.models import Q
            search_filter = Q()
            for field in self.search_fields:
                search_filter |= Q(**{f"{field}__icontains": search_query})
            queryset = queryset.filter(search_filter)

        view_mode = self.request.GET.get('view', 'active') or 'active'
        if view_mode == 'archived':
            queryset = queryset.filter(is_active=False).order_by('-deleted_at')
        elif view_mode == 'active':
            queryset = queryset.filter(is_active=True, status='VALIDATED').order_by('-created_at')
        elif view_mode == 'rejected':
            queryset = queryset.filter(is_active=True, status='REJECTED').order_by('-updated_at')
        else:
            queryset = queryset.filter(is_active=True, status='DRAFT').order_by('-updated_at')

        return queryset.select_related('batch', 'parameter')


class ParameterResultCreateView(AuditTrailMixin, CreateView):
    model = ParameterResult
    form_class = ParameterResultForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class ParameterResultUpdateView(AuditTrailMixin, StatusResetMixin, UpdateView):
    model = ParameterResult
    form_class = ParameterResultForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class ParameterResultDeleteView(GenericDeleteView):
    model = ParameterResult

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class ParameterResultRestoreView(GenericRestoreView):
    model = ParameterResult

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.restore()
        return redirect('batch:batch_logbook', pk=obj.batch.pk)


class ParameterResultDetailView(EntityDetailView):
    model = ParameterResult


class ParameterResultValidateView(EntityValidateView):
    model = ParameterResult

    def post(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        obj.validate_entity(user=request.user)
        return redirect('batch:batch_logbook', pk=obj.batch.pk)


class ParameterResultRejectView(EntityRejectView):
    model = ParameterResult

    def post(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        reason = request.POST.get('rejection_reason')
        if reason:
            obj.status = 'REJECTED'
            obj.rejection_reason = reason
            obj.updated_by = request.user
            obj.save()
        return redirect('batch:batch_logbook', pk=obj.batch.pk)


# ==========================================
# SAMPLE RESULT VIEWS
# ==========================================
class SampleResultListView(FilterStateMixin, ListView):
    model = SampleResult
    template_name = 'batch/sample_result_list.html'
    context_object_name = 'sample_results'
    search_fields = ['batch__name', 'sample__sample_name', 'actual_value']

    def get_queryset(self):
        queryset = ListView.get_queryset(self)
        search_query = self.request.GET.get('q')
        if search_query:
            from django.db.models import Q
            search_filter = Q()
            for field in self.search_fields:
                search_filter |= Q(**{f"{field}__icontains": search_query})
            queryset = queryset.filter(search_filter)

        view_mode = self.request.GET.get('view', 'active') or 'active'
        if view_mode == 'archived':
            queryset = queryset.filter(is_active=False).order_by('-deleted_at')
        elif view_mode == 'active':
            queryset = queryset.filter(is_active=True, status='VALIDATED').order_by('-created_at')
        elif view_mode == 'rejected':
            queryset = queryset.filter(is_active=True, status='REJECTED').order_by('-updated_at')
        else:
            queryset = queryset.filter(is_active=True, status='DRAFT').order_by('-updated_at')

        return queryset.select_related('batch', 'sample')


class SampleResultCreateView(AuditTrailMixin, CreateView):
    model = SampleResult
    form_class = SampleResultForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class SampleResultUpdateView(AuditTrailMixin, StatusResetMixin, UpdateView):
    model = SampleResult
    form_class = SampleResultForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class SampleResultDeleteView(GenericDeleteView):
    model = SampleResult

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class SampleResultRestoreView(GenericRestoreView):
    model = SampleResult

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.restore()
        return redirect('batch:batch_logbook', pk=obj.batch.pk)


class SampleResultDetailView(EntityDetailView):
    model = SampleResult


class SampleResultValidateView(EntityValidateView):
    model = SampleResult

    def post(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        obj.validate_entity(user=request.user)
        return redirect('batch:batch_logbook', pk=obj.batch.pk)


class SampleResultRejectView(EntityRejectView):
    model = SampleResult

    def post(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        reason = request.POST.get('rejection_reason')
        if reason:
            obj.status = 'REJECTED'
            obj.rejection_reason = reason
            obj.updated_by = request.user
            obj.save()
        return redirect('batch:batch_logbook', pk=obj.batch.pk)