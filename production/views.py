from django.http import HttpResponseRedirect, request
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from django.db import transaction
from django.contrib import messages
from django.db.models import Max
from phf.utils import (
    AuditTrailMixin, StatusResetMixin, FilterStateMixin,
    GenericDeleteView, GenericRestoreView, EntityDetailView,
    EntityValidateView, EntityRejectView
)
from referential.models import GlobalUnitOperation
from .models import Process, UnitOperation, Step, Parameter, Sample, SamplingPlan
from .forms import ProcessForm, UnitOperationForm, StepForm, ParameterForm, SampleForm, SamplingPlanForm


# =========================================================================
# 1. PROCESS VIEWS
# =========================================================================
class ProcessListView(FilterStateMixin, ListView):
    model = Process
    template_name = 'production/process_list.html'
    context_object_name = 'processes'
    search_fields = ['name', 'code']


class ProcessCreateView(AuditTrailMixin, CreateView):
    model = Process
    form_class = ProcessForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('production:process_list')


class ProcessUpdateView(AuditTrailMixin, StatusResetMixin, UpdateView):
    model = Process
    form_class = ProcessForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('production:process_list')


class ProcessDeleteView(GenericDeleteView):
    model = Process
    success_url = reverse_lazy('production:process_list')


class ProcessRestoreView(GenericRestoreView):
    model = Process
    redirect_url = 'production:process_list'


class ProcessDetailView(EntityDetailView):
    model = Process

    def get_object(self, queryset=None):
        base_queryset = super().get_queryset()
        optimized_queryset = base_queryset.prefetch_related(
            'units__steps__parameters',
            'units__steps__sampling_plans__samples__analytical_method'
        )
        return get_object_or_404(optimized_queryset, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_process_view'] = True
        return context


class ProcessValidateView(EntityValidateView):
    model = Process
    redirect_url = 'production:process_list'


class ProcessRejectView(EntityRejectView):
    model = Process
    redirect_url = 'production:process_list'


class ProcessSubmitView(View):

    def post(self, request, pk):
        process = get_object_or_404(Process, pk=pk)
        if process.status in ['DRAFT', 'REJECTED']:
            process.status = 'PENDING'
            process.updated_by = request.user
            process.save()
            messages.success(request, f"Process template '{process}' has been submitted for review.")
        return redirect('production:process_list')


class ProcessCreateNewVersionView(View):

    def post(self, request, pk):
        old_process = get_object_or_404(Process, pk=pk)

        if old_process.status != 'VALIDATED':
            messages.error(request, "Only validated templates can be versioned.")
            return redirect('production:process_list')

        with transaction.atomic():
            max_version = Process.objects.filter(
                code=old_process.code
            ).aggregate(Max('version'))['version__max']

            current_max = max_version if max_version is not None else old_process.version
            next_version = current_max + 1

            new_process = Process.objects.create(
                name=old_process.name,
                code=old_process.code,
                scale=old_process.scale,
                version=next_version,
                parent_version=old_process,
                status='DRAFT',
                created_by=request.user,
                updated_by=request.user
            )

            for u in old_process.units.filter(is_active=True):
                new_u = UnitOperation.objects.create(
                    process=new_process,
                    name=u.name,
                    unit_type=u.unit_type,
                    order=u.order,
                    created_by=request.user,
                    updated_by=request.user
                )
                for s in u.steps.filter(is_active=True):
                    new_s = Step.objects.create(
                        unit_operation=new_u,
                        name=s.name,
                        order=s.order,
                        created_by=request.user,
                        updated_by=request.user
                    )

                    for p in s.parameters.filter(is_active=True):
                        Parameter.objects.create(
                            step=new_s,
                            name=p.name,
                            unit=p.unit,
                            format_type=p.format_type,
                            format_low_range=p.format_low_range,
                            format_high_range=p.format_high_range,
                            low_proven_acceptable_range=p.low_proven_acceptable_range,
                            high_proven_acceptable_range=p.high_proven_acceptable_range,
                            low_normal_operating_range=p.low_normal_operating_range,
                            high_normal_operating_range=p.high_normal_operating_range,
                            order=p.order,
                            created_by=request.user,
                            updated_by=request.user
                        )

                    for sample in s.samples.filter(is_active=True):
                        new_sample = Sample.objects.create(
                            step=new_s,
                            sample_name=sample.sample_name,
                            created_by=request.user,
                            updated_by=request.user
                        )
                        active_methods = sample.analytical_methods.filter(is_active=True)
                        new_sample.analytical_methods.set(active_methods)

        messages.success(request, f"New version {new_process.version} initialized successfully in Draft.")
        return redirect('production:process_list')


# =========================================================================
# 2. UNIT OPERATION VIEWS
# =========================================================================
class UnitOperationStructureView(TemplateView):
    template_name = 'production/unitoperation_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        process = get_object_or_404(Process, pk=self.kwargs['process_pk'])
        view_mode = self.request.GET.get('view', 'active')

        if view_mode == 'archived':
            units = UnitOperation.objects.filter(process=process, is_active=False).order_by('order')
        else:
            units = UnitOperation.objects.filter(process=process, is_active=True).order_by('order')

        count_active = UnitOperation.objects.filter(process=process, is_active=True).count()
        count_archived = UnitOperation.objects.filter(process=process, is_active=False).count()

        context.update({
            'process': process,
            'units': units,
            'view_mode': view_mode,
            'count_active': count_active,
            'count_archived': count_archived,
            'form': context.get('form') or UnitOperationForm(),
        })
        return context


class UnitOperationAddView(View):
    def post(self, request, process_pk):
        process = get_object_or_404(Process, pk=process_pk)
        view_mode = request.GET.get('view', 'active')

        form = UnitOperationForm(request.POST)
        form.instance.process = process

        if form.is_valid():
            try:
                unit = form.save(commit=False)
                catalog_item = form.cleaned_data.get('name')

                unit.unit_type = catalog_item.unit_type
                unit.name = catalog_item.name

                max_active_order = UnitOperation.objects.filter(
                    process=process,
                    is_active=True
                ).aggregate(Max('order'))['order__max'] or 0

                unit.order = max_active_order + 1
                unit.created_by = request.user
                unit.updated_by = request.user

                unit.save()

                messages.success(request, f"Operation '{unit.name}' successfully added to flowchart.")
            except Exception as e:
                messages.error(request, f"Error saving unit operation: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"[{field.upper()}] {error}")

        return redirect(f"/production/processes/{process.pk}/structure/?view={view_mode}")


class UnitOperationRestoreView(View):

    def post(self, request, pk):
        unit = get_object_or_404(UnitOperation, pk=pk)
        process_pk = unit.process.pk

        with transaction.atomic():
            try:
                max_active_order = UnitOperation.objects.filter(
                    process=unit.process, is_active=True
                ).aggregate(Max('order'))['order__max'] or 0

                unit.restore()
                unit.order = max_active_order + 1
                unit.save(update_fields=['order'])

                archived_units = UnitOperation.objects.filter(
                    process=unit.process, is_active=False
                ).order_by('order')
                for index, arch_unit in enumerate(archived_units, start=2000000001):
                    if arch_unit.order != index:
                        arch_unit.order = index
                        arch_unit.save(update_fields=['order'])

                messages.success(request,
                                 f"Operation '{unit.name}' restored back to active flowchart at position {unit.order}.")
            except Exception as e:
                messages.error(request, f"Action denied: {str(e)}")

        return redirect(f"/production/processes/{process_pk}/structure/?view=archived")


class UnitOperationReorderView(View):

    def get(self, request, pk, direction):
        unit = get_object_or_404(UnitOperation, pk=pk)
        process = unit.process

        if process.status in ['VALIDATED', 'PENDING']:
            messages.error(request, "Cannot reorder steps while the process structure is locked.")
            return redirect(f"/production/processes/{process.pk}/structure/")

        current_order = unit.order

        with transaction.atomic():
            if direction == 'up':
                target_unit = UnitOperation.objects.filter(
                    process=process, is_active=True, order__lt=current_order
                ).order_by('-order').first()
            else:
                target_unit = UnitOperation.objects.filter(
                    process=process, is_active=True, order__gt=current_order
                ).order_by('order').first()

            if target_unit:
                target_order = target_unit.order

                target_unit.order = 2147483647
                target_unit.save(update_fields=['order'])

                unit.order = target_order
                unit.save(update_fields=['order'])

                target_unit.order = current_order
                target_unit.save(update_fields=['order'])

                storage = messages.get_messages(request)
                storage.used = True
                messages.info(request, "Flowchart sequence updated.")

        return redirect(f"/production/processes/{process.pk}/structure/")


class UnitOperationDetailView(EntityDetailView):
    model = UnitOperation
    template_name = 'generic/generic_detail.html'


class UnitOperationUpdateView(AuditTrailMixin, StatusResetMixin, UpdateView):
    model = UnitOperation
    form_class = UnitOperationForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return f"/production/processes/{self.object.process.pk}/structure/?view=active"


class UnitOperationDeleteView(GenericDeleteView):
    model = UnitOperation

    def get_success_url(self):
        return f"/production/processes/{self.object.process.pk}/structure/?view=active"

    def form_valid(self, form):
        success_url = self.get_success_url()

        with transaction.atomic():
            try:
                self.object.order = 2147483647
                self.object.save(update_fields=['order'])

                self.object.delete(user=self.request.user)

                active_units = UnitOperation.objects.filter(
                    process=self.object.process, is_active=True
                ).order_by('order')

                for index, act_unit in enumerate(active_units, start=1):
                    if act_unit.order != index:
                        act_unit.order = index
                        act_unit.save(update_fields=['order'])

                archived_units = UnitOperation.objects.filter(
                    process=self.object.process, is_active=False
                ).order_by('order')

                for index, arch_unit in enumerate(archived_units, start=2000000001):
                    if arch_unit.order != index:
                        arch_unit.order = index
                        arch_unit.save(update_fields=['order'])

                messages.warning(self.request, f"Operation '{self.object.name}' archived.")

            except Exception as e:
                messages.error(request, f"Action denied: {str(e)}")
                return HttpResponseRedirect(success_url)

        return HttpResponseRedirect(success_url)


# =========================================================================
# 3. STEP VIEWS
# =========================================================================
class StepStructureView(TemplateView):
    template_name = 'production/step_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        unit = get_object_or_404(UnitOperation, pk=self.kwargs['unit_pk'])
        view_mode = self.request.GET.get('view', 'active')

        if view_mode == 'archived':
            steps = Step.objects.filter(unit_operation=unit, is_active=False).order_by('order')
        else:
            steps = Step.objects.filter(unit_operation=unit, is_active=True).order_by('order')

        count_active = Step.objects.filter(unit_operation=unit, is_active=True).count()
        count_archived = Step.objects.filter(unit_operation=unit, is_active=False).count()

        context.update({
            'unit': unit,
            'process': unit.process,
            'steps': steps,
            'view_mode': view_mode,
            'count_active': count_active,
            'count_archived': count_archived,
            'form': context.get('form') or StepForm()
        })
        return context


class StepAddView(View):

    def post(self, request, unit_pk):
        unit = get_object_or_404(UnitOperation, pk=unit_pk)
        view_mode = request.GET.get('view', 'active')

        form = StepForm(request.POST)
        form.instance.unit_operation = unit

        if form.is_valid():
            try:
                step = form.save(commit=False)

                max_active_order = Step.objects.filter(
                    unit_operation=unit,
                    is_active=True
                ).aggregate(Max('order'))['order__max'] or 0

                step.order = max_active_order + 1
                step.created_by = request.user
                step.updated_by = request.user
                step.save()
                messages.success(request, f"Step '{step.name}' successfully added.")
            except Exception as e:
                messages.error(request, f"Error saving step: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"[{field.upper()}] {error}")

        return redirect(f"/production/unit-operations/{unit.pk}/manage/?view={view_mode}")

class StepDeleteView(GenericDeleteView):
    model = Step

    def get_success_url(self):
        return f"/production/unit-operations/{self.object.unit_operation.pk}/manage/?view=active"

    def form_valid(self, form):
        success_url = self.get_success_url()

        with transaction.atomic():
            try:
                self.object.order = 2147483647
                self.object.save(update_fields=['order'])

                self.object.delete(user=self.request.user)

                active_steps = Step.objects.filter(
                    unit_operation=self.object.unit_operation, is_active=True
                ).order_by('order')

                for index, act_step in enumerate(active_steps, start=1):
                    if act_step.order != index:
                        act_step.order = index
                        act_step.save(update_fields=['order'])

                archived_steps = Step.objects.filter(
                    unit_operation=self.object.unit_operation, is_active=False
                ).order_by('order')

                for index, arch_step in enumerate(archived_steps, start=2000000001):
                    if arch_step.order != index:
                        arch_step.order = index
                        arch_step.save(update_fields=['order'])

                messages.warning(self.request,
                                 f"Step '{self.object.name}' archived. Active sequence re-indexed from 1.")

            except Exception as e:
                messages.error(self.request, f"Action denied: {str(e)}")
                return HttpResponseRedirect(success_url)

        return HttpResponseRedirect(success_url)

class StepRestoreView(View):

    def post(self, request, pk):
        step = get_object_or_404(Step, pk=pk)
        unit_pk = step.unit_operation.pk

        with transaction.atomic():
            try:
                max_active_order = Step.objects.filter(
                    unit_operation=step.unit_operation, is_active=True
                ).aggregate(Max('order'))['order__max'] or 0

                step.restore()
                step.order = max_active_order + 1
                step.save(update_fields=['order'])

                archived_steps = Step.objects.filter(
                    unit_operation=step.unit_operation, is_active=False
                ).order_by('order')
                for index, arch_step in enumerate(archived_steps, start=2000000001):
                    if arch_step.order != index:
                        arch_step.order = index
                        arch_step.save(update_fields=['order'])

                messages.success(request, f"Step '{step.name}' restored successfully at position {step.order}.")
            except Exception as e:
                messages.error(request, f"Action denied: {str(e)}")

        return redirect(f"/production/unit-operations/{unit_pk}/manage/?view=archived")


class StepReorderView(View):

    def get(self, request, pk, direction):
        step = get_object_or_404(Step, pk=pk)
        unit = step.unit_operation
        process = unit.process

        if process.status in ['VALIDATED', 'PENDING']:
            messages.error(request, "Cannot reorder steps while the process structure is locked.")
            return redirect(f"/production/unit-operations/{unit.pk}/manage/")

        current_order = step.order

        with transaction.atomic():
            if direction == 'up':
                target_step = Step.objects.filter(
                    unit_operation=unit, is_active=True, order__lt=current_order
                ).order_by('-order').first()
            else:
                target_step = Step.objects.filter(
                    unit_operation=unit, is_active=True, order__gt=current_order
                ).order_by('order').first()

            if target_step:
                target_order = target_step.order

                target_step.order = 2147483647
                target_step.save(update_fields=['order'])

                step.order = target_order
                step.save(update_fields=['order'])

                target_step.order = current_order
                target_step.save(update_fields=['order'])

                storage = messages.get_messages(request)
                storage.used = True
                messages.info(request, "Step sequence updated.")

        return redirect(f"/production/unit-operations/{unit.pk}/manage/")


class StepDetailView(EntityDetailView):
    model = Step
    template_name = 'generic/generic_detail.html'


class StepUpdateView(AuditTrailMixin, StatusResetMixin, UpdateView):
    model = Step
    form_class = StepForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return f"/production/unit-operations/{self.object.unit_operation.pk}/manage/?view=active"


# =========================================================================
# 4. PARAMETER VIEWS
# =========================================================================
class ParameterStructureView(TemplateView):
    template_name = 'production/parameter_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        step = get_object_or_404(Step, pk=self.kwargs['step_pk'])
        view_mode = self.request.GET.get('view', 'active')

        if view_mode == 'archived':
            parameters = Parameter.objects.filter(step=step, is_active=False).order_by('order')
        else:
            parameters = Parameter.objects.filter(step=step, is_active=True).order_by('order')

        count_active = Parameter.objects.filter(step=step, is_active=True).count()
        count_archived = Parameter.objects.filter(step=step, is_active=False).count()

        context.update({
            'step': step,
            'unit': step.unit_operation,
            'process': step.unit_operation.process,
            'parameters': parameters,
            'view_mode': view_mode,
            'count_active': count_active,
            'count_archived': count_archived,
            'form': context.get('form') or ParameterForm()
        })
        return context


class ParameterAddView(View):
    def post(self, request, step_pk):
        step = get_object_or_404(Step, pk=step_pk)
        view_mode = request.GET.get('view', 'active')

        form = ParameterForm(request.POST)
        form.instance.step = step

        if form.is_valid():
            try:
                param = form.save(commit=False)

                max_active_order = Parameter.objects.filter(
                    step=step,
                    is_active=True
                ).aggregate(Max('order'))['order__max'] or 0

                param.order = max_active_order + 1
                param.created_by = request.user
                param.updated_by = request.user
                param.save()
                messages.success(request, f"Parameter '{param.name}' successfully added to step.")
            except Exception as e:
                messages.error(request, f"Error saving parameter: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"[{field.upper()}] {error}")

        return redirect(f"/production/steps/{step.pk}/parameters/?view={view_mode}")


class ParameterDeleteView(GenericDeleteView):
    model = Parameter

    def get_success_url(self):
        return f"/production/steps/{self.object.step.pk}/parameters/?view=active"

    def form_valid(self, form):
        success_url = self.get_success_url()

        with transaction.atomic():
            try:
                self.object.order = 2147483647
                self.object.save(update_fields=['order'])

                self.object.delete(user=self.request.user)

                active_params = Parameter.objects.filter(
                    step=self.object.step, is_active=True
                ).order_by('order')

                for index, act_param in enumerate(active_params, start=1):
                    if act_param.order != index:
                        act_param.order = index
                        act_param.save(update_fields=['order'])

                archived_params = Parameter.objects.filter(
                    step=self.object.step, is_active=False
                ).order_by('order')

                for index, arch_param in enumerate(archived_params, start=2000000001):
                    if arch_param.order != index:
                        arch_param.order = index
                        arch_param.save(update_fields=['order'])

                messages.warning(self.request, f"Parameter '{self.object.name}' archived and sequence re-indexed.")
            except Exception as e:
                messages.error(self.request, f"Action denied: {str(e)}")
                return HttpResponseRedirect(success_url)

        return HttpResponseRedirect(success_url)


class ParameterRestoreView(View):
    def post(self, request, pk):
        param = get_object_or_404(Parameter, pk=pk)
        step_pk = param.step.pk

        with transaction.atomic():
            try:
                max_active_order = Parameter.objects.filter(
                    step=param.step, is_active=True
                ).aggregate(Max('order'))['order__max'] or 0

                param.restore()
                param.order = max_active_order + 1
                param.save(update_fields=['order'])

                archived_params = Parameter.objects.filter(
                    step=param.step, is_active=False
                ).order_by('order')
                for index, arch_param in enumerate(archived_params, start=2000000001):
                    if arch_param.order != index:
                        arch_param.order = index
                        arch_param.save(update_fields=['order'])

                messages.success(request, f"Parameter '{param.name}' restored back at position {param.order}.")
            except Exception as e:
                messages.error(self.request, f"Action denied: {str(e)}")

        return redirect(f"/production/steps/{step_pk}/parameters/?view=archived")


class ParameterReorderView(View):
    def get(self, request, pk, direction):
        param = get_object_or_404(Parameter, pk=pk)
        step = param.step
        process = step.unit_operation.process

        if process.status in ['VALIDATED', 'PENDING']:
            messages.error(request, "Cannot reorder elements while the process structure is locked.")
            return redirect(f"/production/steps/{step.pk}/parameters/")

        current_order = param.order

        with transaction.atomic():
            if direction == 'up':
                target_param = Parameter.objects.filter(
                    step=step, is_active=True, order__lt=current_order
                ).order_by('-order').first()
            else:
                target_param = Parameter.objects.filter(
                    step=step, is_active=True, order__gt=current_order
                ).order_by('order').first()

            if target_param:
                target_order = target_param.order

                target_param.order = 2147483647
                target_param.save(update_fields=['order'])

                param.order = target_order
                param.save(update_fields=['order'])

                target_param.order = current_order
                target_param.save(update_fields=['order'])

                messages.info(request, "Parameters sequence updated.")

        return redirect(f"/production/steps/{step.pk}/parameters/")


class ParameterDetailView(EntityDetailView):
    model = Parameter
    template_name = 'generic/generic_detail.html'


class ParameterUpdateView(AuditTrailMixin, StatusResetMixin, UpdateView):
    model = Parameter
    form_class = ParameterForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return f"/production/steps/{self.object.step.pk}/parameters/?view=active"


# =========================================================================
# 5. SAMPLING PLAN VIEWS
# =========================================================================
class SamplingPlanStructureView(TemplateView):
    template_name = 'production/samplingplan_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        step = get_object_or_404(Step, pk=self.kwargs['step_pk'])
        view_mode = self.request.GET.get('view', 'active')

        if view_mode == 'archived':
            sampling_plans = SamplingPlan.objects.filter(step=step, is_active=False).order_by('created_at')
        else:
            sampling_plans = SamplingPlan.objects.filter(step=step, is_active=True).order_by('created_at')

        count_active = SamplingPlan.objects.filter(step=step, is_active=True).count()
        count_archived = SamplingPlan.objects.filter(step=step, is_active=False).count()

        context.update({
            'step': step,
            'unit': step.unit_operation,
            'process': step.unit_operation.process,
            'sampling_plans': sampling_plans,
            'view_mode': view_mode,
            'count_active': count_active,
            'count_archived': count_archived,
            'form': context.get('form') or SamplingPlanForm()
        })
        return context


class SamplingPlanAddView(View):
    def post(self, request, step_pk):
        step = get_object_or_404(Step, pk=step_pk)
        view_mode = request.GET.get('view', 'active')

        form = SamplingPlanForm(request.POST)
        form.instance.step = step

        if form.is_valid():
            try:
                sampling_plan = form.save(commit=False)
                sampling_plan.created_by = request.user
                sampling_plan.updated_by = request.user
                sampling_plan.save()
                messages.success(request, f"Sampling Plan '{sampling_plan.Name or ''}' successfully added.")
            except Exception as e:
                messages.error(request, f"Error saving sampling plan: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"[{field.upper()}] {error}")

        return redirect(f"/production/steps/{step.pk}/samplingplans/?view={view_mode}")


class SamplingPlanDeleteView(GenericDeleteView):
    model = SamplingPlan

    def get_success_url(self):
        return f"/production/steps/{self.object.step.pk}/samplingplans/?view=active"

    def form_valid(self, form):
        success_url = self.get_success_url()
        try:
            self.object.delete(user=self.request.user)
            messages.warning(self.request, f"Sampling Plan archived.")
        except Exception as e:
            messages.error(self.request, f"Action denied: {str(e)}")
        return HttpResponseRedirect(success_url)


class SamplingPlanRestoreView(View):
    def post(self, request, pk):
        sampling_plan = get_object_or_404(SamplingPlan, pk=pk)
        step_pk = sampling_plan.step.pk
        try:
            sampling_plan.restore()
            messages.success(request, f"Sampling Plan restored successfully.")
        except Exception as e:
            messages.error(request, f"Action denied: {str(e)}")
        return redirect(f"/production/steps/{step_pk}/samplingplans/?view=archived")


class SamplingPlanDetailView(EntityDetailView):
    model = SamplingPlan
    template_name = 'generic/generic_detail.html'


class SamplingPlanUpdateView(AuditTrailMixin, StatusResetMixin, UpdateView):
    model = SamplingPlan
    form_class = SamplingPlanForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return f"/production/steps/{self.object.step.pk}/samplingplans/?view=active"


# =========================================================================
# 6. SAMPLE VIEWS
# =========================================================================
class SampleStructureView(TemplateView):
    template_name = 'production/sample_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sampling_plan = get_object_or_404(SamplingPlan, pk=self.kwargs['sampling_plan_pk'])
        view_mode = self.request.GET.get('view', 'active')

        if view_mode == 'archived':
            samples = Sample.objects.filter(sampling_plan=sampling_plan, is_active=False).order_by('-deleted_at')
        else:
            samples = Sample.objects.filter(sampling_plan=sampling_plan, is_active=True).order_by('created_at')

        count_active = Sample.objects.filter(sampling_plan=sampling_plan, is_active=True).count()
        count_archived = Sample.objects.filter(sampling_plan=sampling_plan, is_active=False).count()

        context.update({
            'sampling_plan': sampling_plan,
            'step': sampling_plan.step,
            'unit': sampling_plan.step.unit_operation,
            'process': sampling_plan.step.unit_operation.process,
            'samples': samples,
            'view_mode': view_mode,
            'count_active': count_active,
            'count_archived': count_archived,
            'form': context.get('form') or SampleForm()
        })
        return context


class SampleAddView(View):
    def post(self, request, sampling_plan_pk):
        sampling_plan = get_object_or_404(SamplingPlan, pk=sampling_plan_pk)
        view_mode = request.GET.get('view', 'active')

        form = SampleForm(request.POST)
        form.instance.sampling_plan = sampling_plan

        if form.is_valid():
            try:
                sample = form.save(commit=False)
                sample.created_by = request.user
                sample.updated_by = request.user
                sample.save()

                messages.success(request, f"Sample '{sample.sample_name}' successfully added.")
            except Exception as e:
                messages.error(request, f"Error saving sample: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"[{field.upper()}] {error}")

        return redirect(f"/production/samplingplans/{sampling_plan.pk}/samples/?view={view_mode}")


class SampleDeleteView(GenericDeleteView):
    model = Sample

    def get_success_url(self):
        return f"/production/samplingplans/{self.object.sampling_plan.pk}/samples/?view=active"

    def form_valid(self, form):
        success_url = self.get_success_url()
        try:
            self.object.delete(user=self.request.user)
            messages.warning(self.request, f"Sample '{self.object.sample_name}' archived.")
        except Exception as e:
            messages.error(self.request, f"Action denied: {str(e)}")
        return HttpResponseRedirect(success_url)


class SampleRestoreView(View):
    def post(self, request, pk):
        sample = get_object_or_404(Sample, pk=pk)
        sampling_plan_pk = sample.sampling_plan.pk
        try:
            sample.restore()
            messages.success(request, f"Sample '{sample.sample_name}' restored successfully.")
        except Exception as e:
            messages.error(request, f"Action denied: {str(e)}")
        return redirect(f"/production/samplingplans/{sampling_plan_pk}/samples/?view=archived")


class SampleDetailView(EntityDetailView):
    model = Sample
    template_name = 'generic/generic_detail.html'


class SampleUpdateView(AuditTrailMixin, StatusResetMixin, UpdateView):
    model = Sample
    form_class = SampleForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return f"/production/samplingplans/{self.object.sampling_plan.pk}/samples/?view=active"