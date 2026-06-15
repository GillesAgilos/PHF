from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from phf.utils import (
    FilterStateMixin, AuditTrailMixin, StatusResetMixin,
    GenericDeleteView, GenericRestoreView, EntityDetailView,
    EntityValidateView, EntityRejectView
)
from .models import Batch, AnalysisResult, ParameterResult
from .forms import BatchForm, ParameterResultForm, AnalysisResultForm
from production.models import UnitOperation, Step, Analysis
from .security import BatchRoleRequiredMixin


# ==========================================
# BATCH VIEWS
# ==========================================
class BatchListView(BatchRoleRequiredMixin, FilterStateMixin, ListView):
    model = Batch
    template_name = 'batch/batch_list.html'
    context_object_name = 'batches'
    search_fields = ['project__name', 'process__code']

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related('project', 'process').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['view_mode'] = self.request.GET.get('view', 'active') or 'active'

        context['count_active'] = Batch.objects.filter(is_active=True, status='VALIDATED').count()
        context['count_archived'] = Batch.objects.filter(is_active=False).count()
        context['count_rejected'] = Batch.objects.filter(is_active=True, status='REJECTED').count()
        context['count_draft'] = Batch.objects.filter(is_active=True, status='DRAFT').count()

        user_group = None
        if self.request.user.is_authenticated and self.request.user.groups.exists():
            user_group = self.request.user.groups.all()[0].name
        context['user_group'] = user_group

        return context


class BatchCreateView(BatchRoleRequiredMixin, AuditTrailMixin, CreateView):
    model = Batch
    form_class = BatchForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('batch:batch_list')


class BatchUpdateView(BatchRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    model = Batch
    form_class = BatchForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('batch:batch_list')


class BatchDeleteView(BatchRoleRequiredMixin, GenericDeleteView):
    model = Batch
    success_url = reverse_lazy('batch:batch_list')


class BatchRestoreView(BatchRoleRequiredMixin, GenericRestoreView):
    model = Batch
    redirect_url = 'batch:batch_list'


class BatchDetailView(BatchRoleRequiredMixin, EntityDetailView):
    model = Batch

    def get_context_data(self, **kwargs):
        if not hasattr(self.model, 'get_authorized_actions'):
            self.model.get_authorized_actions = lambda instance, user: []

        context = super().get_context_data(**kwargs)
        batch = context.get('object') or self.get_object()

        user_groups = self.request.user.groups.values_list('name',
                                                           flat=True) if self.request.user.is_authenticated else []

        if batch and 'dynamic_actions' in context:
            if batch.status == 'VALIDATED':
                context['dynamic_actions'] = [
                    action for action in context['dynamic_actions']
                    if action.get('label') != 'Edit Record'
                ]

            if 'Data_Steward' in user_groups and batch.status == 'DRAFT' and batch.is_active:
                context['dynamic_actions'].extend([
                    {
                        'label': 'Validate',
                        'url': reverse('batch:batch_validate', kwargs={'pk': batch.pk}),
                        'class': 'btn-success btn-sm',
                        'icon': 'bi bi-check-circle'
                    },
                    {
                        'label': 'Reject',
                        'url': reverse('batch:batch_reject', kwargs={'pk': batch.pk}),
                        'class': 'btn-danger btn-sm',
                        'icon': 'bi bi-x-circle',
                        'target': '#rejectModal'
                    }
                ])
        return context


class BatchValidateView(BatchRoleRequiredMixin, EntityValidateView):
    model = Batch
    redirect_url = 'batch:batch_list'

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(Batch, pk=kwargs.get('pk'))

        try:
            obj.validate_entity(user=request.user)
            messages.success(request, f"The batch {obj.name} has been successfully validated.")

        except ValidationError as e:
            for msg in e.messages:
                messages.error(request, msg)

        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")

        return redirect('batch:batch_detail', pk=obj.pk)


class BatchRejectView(BatchRoleRequiredMixin, EntityRejectView):
    model = Batch
    redirect_url = 'batch:batch_list'


class BatchLogbookView(BatchRoleRequiredMixin, DetailView):
    model = Batch
    template_name = 'batch/batch_logbook.html'
    context_object_name = 'batch'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batch = self.object
        process = batch.process

        user_group = None
        if self.request.user.is_authenticated and self.request.user.groups.exists():
            user_group = self.request.user.groups.all()[0].name
        context['user_group'] = user_group

        units = UnitOperation.objects.filter(process=process, is_active=True).order_by('order')

        analyses_with_methods = Analysis.objects.filter(is_active=True).select_related('analytical_method')

        steps = Step.objects.filter(unit_operation__in=units, is_active=True).order_by('order').prefetch_related(
            'parameters',
            Prefetch('samples__analyses', queryset=analyses_with_methods)
        )

        param_results = {res.parameter_id: res for res in ParameterResult.objects.filter(batch=batch, is_active=True)}

        analysis_results = {res.analysis_id: res for res in AnalysisResult.objects.filter(batch=batch, is_active=True)}

        process_tree = []
        for unit in units:
            unit_data = {'object': unit, 'steps': []}
            unit_steps = [s for s in steps if s.unit_operation_id == unit.pk]

            for step in unit_steps:
                step_data = {
                    'object': step,
                    'parameters_with_results': [],
                    'analyses_with_results': []
                }

                for param in step.parameters.all():
                    step_data['parameters_with_results'].append({
                        'parameter': param,
                        'unit': param.unit,
                        'result': param_results.get(param.pk)
                    })

                for sample in step.samples.all():
                    for analysis in sample.analyses.all():
                        step_data['analyses_with_results'].append({
                            'analysis': analysis,
                            'unit': analysis.analytical_method.unit if analysis.analytical_method else None,
                            'result': analysis_results.get(analysis.pk)
                        })
                unit_data['steps'].append(step_data)
            process_tree.append(unit_data)

        context['process_tree'] = process_tree
        return context


# ==========================================
# PARAMETER RESULT VIEWS
# ==========================================
class ParameterResultListView(BatchRoleRequiredMixin, FilterStateMixin, ListView):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['view_mode'] = self.request.GET.get('view', 'active') or 'active'

        context['count_active'] = ParameterResult.objects.filter(is_active=True, status='VALIDATED').count()
        context['count_archived'] = ParameterResult.objects.filter(is_active=False).count()
        context['count_rejected'] = ParameterResult.objects.filter(is_active=True, status='REJECTED').count()
        context['count_draft'] = ParameterResult.objects.filter(is_active=True, status='DRAFT').count()

        user_group = None
        if self.request.user.is_authenticated and self.request.user.groups.exists():
            user_group = self.request.user.groups.all()[0].name
        context['user_group'] = user_group

        return context


class ParameterResultCreateView(BatchRoleRequiredMixin, AuditTrailMixin, CreateView):
    model = ParameterResult
    form_class = ParameterResultForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class ParameterResultUpdateView(BatchRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    model = ParameterResult
    form_class = ParameterResultForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class ParameterResultDeleteView(BatchRoleRequiredMixin, GenericDeleteView):
    model = ParameterResult

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class ParameterResultRestoreView(BatchRoleRequiredMixin, GenericRestoreView):
    model = ParameterResult

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.restore()
        return redirect('batch:batch_logbook', pk=obj.batch.pk)


class ParameterResultDetailView(BatchRoleRequiredMixin, EntityDetailView):
    model = ParameterResult

    def get_context_data(self, **kwargs):
        if not hasattr(self.model, 'get_authorized_actions'):
            self.model.get_authorized_actions = lambda instance, user: []

        context = super().get_context_data(**kwargs)
        result = context.get('object') or self.get_object()
        user_groups = self.request.user.groups.values_list('name',
                                                           flat=True) if self.request.user.is_authenticated else []

        if result and 'dynamic_actions' in context:
            if result.status == 'VALIDATED':
                context['dynamic_actions'] = [
                    action for action in context['dynamic_actions']
                    if action.get('label') != 'Edit Record'
                ]

            if 'Data_Steward' in user_groups and result.status == 'DRAFT' and result.is_active:
                context['dynamic_actions'].extend([
                    {
                        'label': 'Validate',
                        'url': reverse('batch:parameter_result_validate', kwargs={'pk': result.pk}),
                        'class': 'btn-success btn-sm',
                        'icon': 'bi bi-check-circle'
                    },
                    {
                        'label': 'Reject',
                        'url': reverse('batch:parameter_result_reject', kwargs={'pk': result.pk}),
                        'class': 'btn-danger btn-sm',
                        'icon': 'bi bi-x-circle',
                        'target': '#rejectModal'
                    }
                ])
        return context


class ParameterResultValidateView(BatchRoleRequiredMixin, EntityValidateView):
    model = ParameterResult

    def post(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        obj.validate_entity(user=request.user)
        return redirect('batch:batch_logbook', pk=obj.batch.pk)


class ParameterResultRejectView(BatchRoleRequiredMixin, EntityRejectView):
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
# ANALYSIS RESULT VIEWS
# ==========================================
class AnalysisResultListView(BatchRoleRequiredMixin, FilterStateMixin, ListView):
    model = AnalysisResult
    template_name = 'batch/analysis_result_list.html'
    context_object_name = 'analysis_results'
    search_fields = ['batch__name', 'analysis__analysis_name', 'actual_value']

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

        return queryset.select_related('batch', 'analysis')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['view_mode'] = self.request.GET.get('view', 'active') or 'active'

        context['count_active'] = AnalysisResult.objects.filter(is_active=True, status='VALIDATED').count()
        context['count_archived'] = AnalysisResult.objects.filter(is_active=False).count()
        context['count_rejected'] = AnalysisResult.objects.filter(is_active=True, status='REJECTED').count()
        context['count_draft'] = AnalysisResult.objects.filter(is_active=True, status='DRAFT').count()

        user_group = None
        if self.request.user.is_authenticated and self.request.user.groups.exists():
            user_group = self.request.user.groups.all()[0].name
        context['user_group'] = user_group

        return context


class AnalysisResultCreateView(BatchRoleRequiredMixin, AuditTrailMixin, CreateView):
    model = AnalysisResult
    form_class = AnalysisResultForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class AnalysisResultUpdateView(BatchRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    model = AnalysisResult
    form_class = AnalysisResultForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class AnalysisResultDeleteView(BatchRoleRequiredMixin, GenericDeleteView):
    model = AnalysisResult

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class AnalysisResultRestoreView(BatchRoleRequiredMixin, GenericRestoreView):
    model = AnalysisResult

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.restore()
        return redirect('batch:batch_logbook', pk=obj.batch.pk)


class AnalysisResultDetailView(BatchRoleRequiredMixin, EntityDetailView):
    model = AnalysisResult

    def get_context_data(self, **kwargs):
        if not hasattr(self.model, 'get_authorized_actions'):
            self.model.get_authorized_actions = lambda instance, user: []

        context = super().get_context_data(**kwargs)
        result = context.get('object') or self.get_object()
        user_groups = self.request.user.groups.values_list('name',
                                                           flat=True) if self.request.user.is_authenticated else []

        if result and 'dynamic_actions' in context:
            if result.status == 'VALIDATED':
                context['dynamic_actions'] = [
                    action for action in context['dynamic_actions']
                    if action.get('label') != 'Edit Record'
                ]

            if 'Data_Steward' in user_groups and result.status == 'DRAFT' and result.is_active:
                context['dynamic_actions'].extend([
                    {
                        'label': 'Validate',
                        'url': reverse('batch:analysis_result_validate', kwargs={'pk': result.pk}),
                        'class': 'btn-success btn-sm',
                        'icon': 'bi bi-check-circle'
                    },
                    {
                        'label': 'Reject',
                        'url': reverse('batch:analysis_result_reject', kwargs={'pk': result.pk}),
                        'class': 'btn-danger btn-sm',
                        'icon': 'bi bi-x-circle',
                        'target': '#rejectModal'
                    }
                ])
        return context


class AnalysisResultValidateView(BatchRoleRequiredMixin, EntityValidateView):
    model = AnalysisResult

    def post(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        obj.validate_entity(user=request.user)
        return redirect('batch:batch_logbook', pk=obj.batch.pk)


class AnalysisResultRejectView(BatchRoleRequiredMixin, EntityRejectView):
    model = AnalysisResult

    def post(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        reason = request.POST.get('rejection_reason')
        if reason:
            obj.status = 'REJECTED'
            obj.rejection_reason = reason
            obj.updated_by = request.user
            obj.save()
        return redirect('batch:batch_logbook', pk=obj.batch.pk)