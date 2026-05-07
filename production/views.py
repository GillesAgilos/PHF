from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import Process, UnitOperation, Step, Parameter
from .forms import ProcessForm, UnitOperationForm, StepForm, ParameterForm


# ==========================================
# MIXIN FOR AUDIT TRAIL
# ==========================================
class AuditTrailMixin:
    def form_valid(self, form):
        if not form.instance.pk:
            form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        if form.instance.pk:
            current_obj = self.model.objects.filter(pk=form.instance.pk).first()
            if current_obj and not current_obj.is_active:
                messages.error(self.request, f"Error: This {self.model.__name__} is archived.")
                return redirect(self.success_url)
        return super().form_valid(form)


# ==========================================
# PROCESS VIEWS
# ==========================================

class ProcessListView(ListView):
    model = Process
    template_name = 'production/process_list.html'
    context_object_name = 'processes'
    queryset = Process.objects.all().order_by('-is_active', 'code')


class ProcessCreateView(AuditTrailMixin, CreateView):
    model = Process
    form_class = ProcessForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('production:process_list')


class ProcessUpdateView(AuditTrailMixin, UpdateView):
    model = Process
    form_class = ProcessForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('production:process_list')


class ProcessDeleteView(DeleteView):
    model = Process
    template_name = 'generic/generic_confirm_delete.html'
    success_url = reverse_lazy('production:process_list')

    def form_valid(self, form):
        self.object.delete(user=self.request.user)
        messages.success(self.request, "Process archived successfully.")
        return HttpResponseRedirect(self.success_url)


class ProcessRestoreView(View):
    def post(self, request, pk):
        obj = get_object_or_404(Process, pk=pk)
        obj.restore()
        messages.success(request, "Process restored successfully.")
        return redirect('production:process_list')


# ==========================================
# UNIT OPERATION VIEWS
# ==========================================

class UnitOperationManageView(ListView):
    model = UnitOperation
    template_name = 'production/process_structure_manage.html'
    context_object_name = 'steps'

    def get_queryset(self):
        return UnitOperation.objects.filter(
            process_id=self.kwargs['process_pk']
        ).order_by('order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        process = get_object_or_404(Process, pk=self.kwargs['process_pk'])
        context['process'] = process
        context['form'] = UnitOperationForm(process=process)
        return context


class UnitOperationCreateView(AuditTrailMixin, CreateView):
    model = UnitOperation
    form_class = UnitOperationForm
    template_name = 'production/process_structure_manage.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['process'] = get_object_or_404(Process, pk=self.kwargs['process_pk'])
        return kwargs

    def form_valid(self, form):
        process = get_object_or_404(Process, pk=self.kwargs['process_pk'])
        form.instance.process = process
        return super().form_valid(form)

    def form_invalid(self, form):
        process = get_object_or_404(Process, pk=self.kwargs['process_pk'])
        steps = UnitOperation.objects.filter(process=process).order_by('order')

        messages.error(self.request, "Operation failed. Please check the errors below.")

        return self.render_to_response(self.get_context_data(
            form=form,
            process=process,
            steps=steps
        ))

    def get_success_url(self):
        return reverse_lazy('production:unit_manage', kwargs={'process_pk': self.kwargs['process_pk']})

class UnitOperationDeleteView(DeleteView):
    model = UnitOperation
    template_name = 'generic/generic_confirm_delete.html'

    def form_valid(self, form):
        process_pk = self.object.process.pk
        self.object.delete(user=self.request.user)
        messages.success(self.request, "Unit Operation removed.")
        return HttpResponseRedirect(
            reverse_lazy('production:unit_manage', kwargs={'process_pk': process_pk})
        )

class UnitReorderView(View):
    def get(self, request, pk, direction):
        unit = get_object_or_404(UnitOperation, pk=pk)
        current_order = unit.order

        if direction == 'up':
            target = UnitOperation.objects.filter(
                process=unit.process,
                order__lt=current_order
            ).order_by('-order').first()
        else:
            target = UnitOperation.objects.filter(
                process=unit.process,
                order__gt=current_order
            ).order_by('order').first()

        if target:
            try:
                with transaction.atomic():
                    old_order = unit.order
                    new_order = target.order

                    # temporary order to facilitate changes
                    unit.order = 9999
                    unit.save()

                    target.order = old_order
                    target.save()

                    unit.order = new_order
                    unit.save()
            except IntegrityError:
                messages.error(request, "Error during reordering.")

        return redirect('production:unit_manage', process_pk=unit.process.pk)

# ==========================================
# STEPS VIEWS
# ==========================================

class StepManageView(ListView):
    model = Step
    template_name = 'production/step_manage.html'
    context_object_name = 'steps'

    def get_queryset(self):
        return Step.objects.filter(unit_operation_id=self.kwargs['unit_pk'], is_active=True).order_by('order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        unit = get_object_or_404(UnitOperation, pk=self.kwargs['unit_pk'])
        context['unit'] = unit
        context['process'] = unit.process
        context['form'] = StepForm(unit_operation=unit)
        return context


class StepCreateView(AuditTrailMixin, CreateView):
    model = Step
    form_class = StepForm
    template_name = 'production/step_manage.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['unit_operation'] = get_object_or_404(UnitOperation, pk=self.kwargs['unit_pk'])
        return kwargs

    def form_valid(self, form):
        form.instance.unit_operation = get_object_or_404(UnitOperation, pk=self.kwargs['unit_pk'])
        return super().form_valid(form)

    def form_invalid(self, form):
        unit = get_object_or_404(UnitOperation, pk=self.kwargs['unit_pk'])
        steps = Step.objects.filter(unit_operation=unit, is_active=True).order_by('order')

        return self.render_to_response(self.get_context_data(
            form=form,
            unit=unit,
            process=unit.process,
            steps=steps
        ))

    def get_success_url(self):
        return reverse_lazy('production:step_manage', kwargs={'unit_pk': self.kwargs['unit_pk']})


class StepReorderView(View):
    def get(self, request, pk, direction):
        step = get_object_or_404(Step, pk=pk)
        current_order = step.order
        if direction == 'up':
            target = Step.objects.filter(unit_operation=step.unit_operation, order__lt=current_order,
                                         is_active=True).order_by('-order').first()
        else:
            target = Step.objects.filter(unit_operation=step.unit_operation, order__gt=current_order,
                                         is_active=True).order_by('order').first()

        if target:
            with transaction.atomic():
                old_order, new_order = step.order, target.order
                step.order = 9999
                step.save()
                target.order = old_order
                target.save()
                step.order = new_order
                step.save()
        return redirect('production:step_manage', unit_pk=step.unit_operation.pk)


class StepDeleteView(DeleteView):
    model = Step

    def form_valid(self, form):
        unit_pk = self.object.unit_operation.pk
        self.object.delete(user=self.request.user)
        return redirect('production:step_manage', unit_pk=unit_pk)


# ==========================================
# PARAMETER VIEWS
# ==========================================

class ParameterManageView(ListView):
    model = Parameter
    template_name = 'production/parameter_manage.html'
    context_object_name = 'params'

    def get_queryset(self):
        return Parameter.objects.filter(step_id=self.kwargs['step_pk'], is_active=True).order_by('order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        step = get_object_or_404(Step, pk=self.kwargs['step_pk'])
        context['step'] = step
        context['unit'] = step.unit_operation
        context['process'] = step.unit_operation.process
        context['form'] = ParameterForm(step=step)
        return context

class ParameterCreateView(AuditTrailMixin, CreateView):
    model = Parameter
    form_class = ParameterForm
    template_name = 'production/parameter_manage.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['step'] = get_object_or_404(Step, pk=self.kwargs['step_pk'])
        return kwargs

    def form_valid(self, form):
        form.instance.step = get_object_or_404(Step, pk=self.kwargs['step_pk'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('production:parameter_manage', kwargs={'step_pk': self.kwargs['step_pk']})

class ParameterReorderView(View):
    def get(self, request, pk, direction):
        param = get_object_or_404(Parameter, pk=pk)
        current_order = param.order
        if direction == 'up':
            target = Parameter.objects.filter(step=param.step, order__lt=current_order, is_active=True).order_by(
                '-order').first()
        else:
            target = Parameter.objects.filter(step=param.step, order__gt=current_order, is_active=True).order_by(
                'order').first()

        if target:
            with transaction.atomic():
                old_order, new_order = param.order, target.order
                param.order = 9999
                param.save()
                target.order = old_order
                target.save()
                param.order = new_order
                param.save()
        return redirect('production:parameter_manage', step_pk=param.step.pk)

class ParameterDeleteView(DeleteView):
    model = Parameter

    def form_valid(self, form):
        step_pk = self.object.step.pk
        self.object.delete(user=self.request.user)
        return redirect('production:parameter_manage', step_pk=step_pk)