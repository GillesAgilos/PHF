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
    EntityValidateView, EntityRejectView, ProcessLockRequiredMixin
)
from .models import Process, UnitOperation, Step, Parameter, Analysis, Sample
from .forms import ProcessForm, UnitOperationForm, StepForm, ParameterForm, SampleForm, AnalysisForm
from .security import ProductionRoleRequiredMixin


# =========================================================================
# 1. PROCESS VIEWS
# =========================================================================
class ProcessListView(ProductionRoleRequiredMixin, FilterStateMixin, ListView):
    """
    Represents a view for displaying a list of Process objects.

    This class extends functionality from several mixins and ListView to
    provide a filtered and searchable list of Process objects intended for
    use in production environments. The view utilizes a specified template
    and context variable to render and manage display logic. It restricts
    access to users with appropriate production roles.

    Attributes:
        model (type): The model associated with this view (Process).
        template_name (str): The path to the template used to render the view.
        context_object_name (str): The name of the context variable containing
            the list of processes.
        search_fields (list of str): Fields that can be searched within the list
            of Process objects.
    """
    model = Process
    template_name = 'production/process_list.html'
    context_object_name = 'processes'
    search_fields = ['name', 'code']


class ProcessCreateView(ProductionRoleRequiredMixin, AuditTrailMixin, CreateView):
    """
    Represents a view for creating a new Process object.

    This class combines functionality for enforcing production-specific role
    permissions, audit trail logging, and form handling for creating a new
    Process object within the application. It leverages the CreateView
    generic class-based view to handle the creation logic, and it integrates
    mixins for additional functionality such as access control and activity
    tracking. The view also defines the form used for submission, the success
    redirect URL, and the template for rendering the form.

    Attributes:
        model (Model): The model that this view will handle, which is the
            Process model.
        form_class (Form): The form class used for rendering the form and
            processing data submission, which is the ProcessForm.
        template_name (str): The path to the template used for rendering the
            create form, defined as 'generic/generic_form.html'.
        success_url (str): The URL to redirect to upon successful creation
            of a Process object, defined using reverse_lazy as
            'production:process_list'.
    """
    model = Process
    form_class = ProcessForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('production:process_list')


class ProcessUpdateView(ProductionRoleRequiredMixin, ProcessLockRequiredMixin,AuditTrailMixin, StatusResetMixin, UpdateView):
    """
    Handles the update operation for a Process instance.

    The class combines multiple mixins to enforce role-based access, lock
    requirements, audit trail handling, and status resetting for the Process model.
    It utilizes a form for process updates and manages the functionality for
    rendering the form, processing the update, and redirecting to a success URL
    upon completion.

    Attributes:
        model (Process): The model associated with this view.
        form_class (ProcessForm): The form class used for updating a Process
            instance.
        template_name (str): Path to the template used for rendering the view's
            form.
        success_url (str): URL to redirect to upon successful update.
    """
    model = Process
    form_class = ProcessForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('production:process_list')


class ProcessDeleteView(ProductionRoleRequiredMixin, ProcessLockRequiredMixin,GenericDeleteView):
    """View for handling the deletion of a Process object.

    This view ensures that only users with appropriate production roles
    and access to the necessary process lock can delete a Process object.
    Inherits functionality from `GenericDeleteView` to handle standard
    DELETE operations and redirect users upon successful deletion.

    Attributes:
        model (Type[Process]): The model associated with this view. Defines
            the `Process` object being deleted.
        success_url (str): URL to redirect to upon successful deletion. Points
            to the process list view.
    """
    model = Process
    success_url = reverse_lazy('production:process_list')


class ProcessRestoreView(ProductionRoleRequiredMixin, GenericRestoreView):
    """
    Handles the restoration of Process objects in the application.

    This class provides functionality for restoring Process instances that may
    have been deleted or deactivated. It enforces production role requirements
    to restrict access and also defines a redirection URL for successful restore
    operations.

    Attributes:
        model (type): The model class to be used for restoration. Represents
            the Process model.
        redirect_url (str): The URL to redirect to after a successful
            restoration operation.
    """
    model = Process
    redirect_url = 'production:process_list'


class ProcessDetailView(ProductionRoleRequiredMixin, EntityDetailView):
    """
    View for displaying detailed information about a Process.

    This class extends generic entity detail functionality and integrates production role-specific
    permissions. It optimizes query performance for related data and provides additional
    context for rendering the Process detail view.

    Attributes:
        model (Process): The Django model representing the entity for this view.
    """
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

        process = context.get('object') or self.get_object()

        context['show_validation_buttons'] = (process.status == Process.Status.PENDING)
        context['show_submit_button'] = (process.status in [Process.Status.DRAFT, Process.Status.REJECTED])
        
        if 'dynamic_actions' in context and process.status in [Process.Status.VALIDATED, Process.Status.PENDING]:
            context['dynamic_actions'] = [
                action for action in context['dynamic_actions']
                if action.get('label') != 'Edit Record'
            ]

        return context


class ProcessValidateView(ProductionRoleRequiredMixin, EntityValidateView):
    """
    View for validating a process in the production workflow.

    This class handles the validation of a process in the production system. It requires
    the user to have the appropriate production role. The validation is only allowed
    for processes with a "PENDING" status. For other statuses, an error message is displayed,
    and the user is redirected to the process list.

    Attributes:
        model (type): The model class representing the process to be validated.
        redirect_url (str): The URL to redirect the user to if the validation fails.
    """
    model = Process
    redirect_url = 'production:process_list'

    def post(self, request, *args, **kwargs):
        process = get_object_or_404(self.model, pk=kwargs.get('pk'))

        if process.status != Process.Status.PENDING:
            messages.error(request, "This process template cannot be validated because it is not pending review.")
            return redirect(self.redirect_url)

        return super().post(request, *args, **kwargs)


class ProcessRejectView(ProductionRoleRequiredMixin, EntityRejectView):
    """
    View for handling rejection of a process in the production workflow.

    This class ensures that only users with the required production roles can
    perform the reject operation on a process entity. The view validates the
    status of the process before allowing it to be rejected. If the process is
    not in a pending review state, it prevents rejection and displays an error
    message to the user.

    Attributes:
        model (type): The model class associated with the process.
        redirect_url (str): The URL to redirect to after a failed or successful
            rejection attempt.
    """
    model = Process
    redirect_url = 'production:process_list'

    def post(self, request, *args, **kwargs):
        process = get_object_or_404(self.model, pk=kwargs.get('pk'))

        if process.status != Process.Status.PENDING:
            messages.error(request, "This process template cannot be rejected because it is not pending review.")
            return redirect(self.redirect_url)

        return super().post(request, *args, **kwargs)

class ProcessSubmitView(ProductionRoleRequiredMixin, View):
    """
    Handles submission of a process for review by changing its status.

    This class-based view allows the submission of process templates for review.
    Only users with the required production role can use this functionality.
    The status of a process is updated to 'PENDING' if it is currently in 'DRAFT'
    or 'REJECTED' status. A success message is displayed upon submission, and the
    user is redirected to the process list view.

    Attributes:
        None
    """
    def post(self, request, pk):
        process = get_object_or_404(Process, pk=pk)
        if process.status in ['DRAFT', 'REJECTED']:
            process.status = 'PENDING'
            process.updated_by = request.user
            process.save()
            messages.success(request, f"Process template '{process}' has been submitted for review.")
        return redirect('production:process_list')


class ProcessCreateNewVersionView(ProductionRoleRequiredMixin, View):
    """
    Handles the creation of a new version of a validated production process.

    This view allows users with the necessary production role to create a new version
    of an existing process template. It duplicates the process, including its units, steps,
    parameters, samples, and their associated analyses. Only processes with a status of
    'VALIDATED' can be versioned. The new version is created in 'DRAFT' status and is
    initialized with all relevant data copied from the previous version.

    Attributes:
        None
    """
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

                    for plan in s.samples.filter(is_active=True):
                        new_plan = Sample.objects.create(
                            step=new_s,
                            name=plan.name,
                            created_by=request.user,
                            updated_by=request.user
                        )

                        for sample in plan.analyses.filter(is_active=True):
                            Analysis.objects.create(

                                sample=new_plan,
                                analysis_name=sample.analysis_name,
                                analytical_method=sample.analytical_method,
                                created_by=request.user,
                                updated_by=request.user
                            )

        messages.success(request, f"New version {new_process.version} initialized successfully in Draft.")
        return redirect('production:process_list')


# =========================================================================
# 2. UNIT OPERATION VIEWS
# =========================================================================
class UnitOperationStructureView(ProductionRoleRequiredMixin, TemplateView):
    """View to manage and display the structure of unit operations in a process.

    This view facilitates the display of unit operations associated with a particular
    process. It supports viewing both active and archived unit operations, along
    with additional context such as the count of active and archived operations,
    the user's associated group, and a form for creating or modifying
    unit operations.

    Attributes:
        template_name (str): Path to the template used for rendering the unit
            operation list.
    """
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

        user_group = None
        if self.request.user.is_authenticated and self.request.user.groups.exists():
            user_group = self.request.user.groups.all()[0].name

        context.update({
            'process': process,
            'units': units,
            'view_mode': view_mode,
            'count_active': count_active,
            'count_archived': count_archived,
            'user_group': user_group,
            'form': context.get('form') or UnitOperationForm(),
        })
        return context


class UnitOperationAddView(ProductionRoleRequiredMixin, View):
    """
    Handles the addition of a unit operation to a process flowchart.

    This class-based view allows users with the necessary production role permissions
    to add new unit operations to a specific process. The operation's order is determined
    based on other active operations within the process. Feedback messages are displayed
    to the user depending on the success or failure of the operation's creation.

    Methods:
        post: Handles POST requests for adding a unit operation to a process.

    Attributes:
        None
    """
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


class UnitOperationRestoreView(ProductionRoleRequiredMixin, View):
    """
    Handles the restoration of an archived UnitOperation back to the active flowchart
    within a specific process.

    This view facilitates the process of restoring a `UnitOperation` instance by updating
    its order to the next available position in the active flowchart. It ensures the
    integrity of the order for both active and archived `UnitOperation` instances within
    the same process.

    Attributes:
        None
    """
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


class UnitOperationReorderView(ProductionRoleRequiredMixin, View):
    """
    Handles the reordering of unit operations within a production process.

    This class is a view that allows the reordering of steps (units) in a production
    process unless the process is in a locked state, such as 'VALIDATED' or 'PENDING'.
    The ordering is performed atomically to ensure data consistency. It ensures that
    the sequence of flow in the production process can be updated dynamically.

    Attributes:
        None
    """
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


class UnitOperationDetailView(ProductionRoleRequiredMixin, EntityDetailView):
    """View for displaying the details of a UnitOperation.

    This class serves as a detail view for a UnitOperation instance, extending
    functionality from `EntityDetailView`. It enforces a role-based access control
    by integrating `ProductionRoleRequiredMixin`. The view customizes the context
    data to include dynamic actions based on the status of the related process.

    Attributes:
        model (UnitOperation): The model associated with this view.
        template_name (str): The name of the template used for rendering the view.
    """
    model = UnitOperation
    template_name = 'generic/generic_detail.html'

    def get_context_data(self, **kwargs):
        if not hasattr(self.model, 'get_authorized_actions'):
            self.model.get_authorized_actions = lambda instance, user: []

        context = super().get_context_data(**kwargs)

        unit = context.get('object')

        if unit and unit.process and 'dynamic_actions' in context:
            if unit.process.status in ['VALIDATED', 'PENDING']:
                context['dynamic_actions'] = [
                    action for action in context['dynamic_actions']
                    if action.get('label') != 'Edit Record'
                ]

        return context


class UnitOperationUpdateView(ProductionRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    """
    Handles the update view for a UnitOperation object.

    This class is responsible for rendering a form to update an existing UnitOperation,
    validating the provided input, saving the updates, and redirecting the user upon
    successful completion. It ensures that appropriate permissions are enforced through
    the use of mixins and maintains an audit trail for changes.

    Attributes:
        model (Model): The model associated with this view, representing a unit operation.
        form_class (Form): The form class used to render and validate the input.
        template_name (str): The path to the HTML template for rendering the form.
    """
    model = UnitOperation
    form_class = UnitOperationForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return f"/production/processes/{self.object.process.pk}/structure/?view=active"


class UnitOperationDeleteView(ProductionRoleRequiredMixin, GenericDeleteView):
    """
    Handles the deletion of a UnitOperation object from the database and updates the
    ordering of other UnitOperation objects in the relevant process.

    This view provides functionality to archive a specific UnitOperation object, reassign
    orders for the active and archived UnitOperation objects within the same process,
    and display relevant user messages upon completion.

    Attributes:
        model (type): The model associated with this view, which is `UnitOperation`.
    """
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
class StepStructureView(ProductionRoleRequiredMixin, TemplateView):
    """
    View that displays a list of steps in a unit operation with filtering options.

    This view retrieves and displays step data associated with a specific unit operation,
    allowing users to filter between active and archived steps. It also provides contextual
    information such as the user's group, counts of active and archived steps, and associated forms.

    Attributes:
        template_name (str): Path to the HTML template used to render the view.
    """
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

        user_group = None
        if self.request.user.is_authenticated and self.request.user.groups.exists():
            user_group = self.request.user.groups.all()[0].name

        context.update({
            'unit': unit,
            'process': unit.process,
            'steps': steps,
            'view_mode': view_mode,
            'count_active': count_active,
            'count_archived': count_archived,
            'user_group': user_group,
            'form': context.get('form') or StepForm()
        })
        return context


class StepAddView(ProductionRoleRequiredMixin, View):
    """
    Handles the addition of a new step to a unit operation in a production system.

    This view is responsible for processing the form submission to add a new step to
    a specific unit operation. It validates the input data, assigns necessary metadata,
    and updates the ordering of active steps for proper positioning. In case of form
    errors or system issues, appropriate messages are displayed to the user.

    Attributes:
        None
    """
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

class StepDeleteView(ProductionRoleRequiredMixin, GenericDeleteView):
    """
    View class to handle the deletion of Step objects with extended functionality.

    This class ensures that steps associated with a unit operation are properly
    archived, and active and archived sequences are re-indexed after deletion.
    It also manages user notifications for successful and failed deletion actions.

    Attributes:
        model (Step): The database model associated with this view.
    """
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

class StepRestoreView(ProductionRoleRequiredMixin, View):
    """
    Handles the restoration of archived steps within a unit operation.

    This class is responsible for restoring archived steps in a production
    environment. When a step is restored, it is marked as active, assigned a
    new order, and properly re-added to the active steps list. Any archived
    steps with altered order due to gaps are adjusted accordingly. Messages
    are displayed to indicate the success or failure of the operation.

    Attributes:
        None
    """
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


class StepReorderView(ProductionRoleRequiredMixin, View):
    """
    Provides functionality to reorder steps within a production unit operation.

    This view allows steps within a production process to be reordered by moving
    a specific step up or down in the sequence. The reordering is only permitted
    if the process status allows modification of its structure. Once the reordering
    is completed, an appropriate message is displayed to the user.

    Attributes:
        None
    """
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


class StepDetailView(ProductionRoleRequiredMixin, EntityDetailView):
    """
    Represents the detailed view for a specific Step in the production process.

    The StepDetailView class inherits from both ProductionRoleRequiredMixin and EntityDetailView.
    It is designed to display detailed information about a specific Step object in a template.
    Additionally, it customizes the context data to filter out certain dynamic actions based on
    the status of the associated process.

    Attributes:
        model (Step): The model associated with this view.
        template_name (str): The template used to render the detailed view.
    """
    model = Step
    template_name = 'generic/generic_detail.html'

    def get_context_data(self, **kwargs):
        if not hasattr(self.model, 'get_authorized_actions'):
            self.model.get_authorized_actions = lambda instance, user: []

        context = super().get_context_data(**kwargs)
        step = context.get('object')

        if step and step.unit_operation and step.unit_operation.process and 'dynamic_actions' in context:
            process_status = step.unit_operation.process.status
            if process_status in ['VALIDATED', 'PENDING']:
                context['dynamic_actions'] = [
                    action for action in context['dynamic_actions']
                    if action.get('label') != 'Edit Record'
                ]

        return context


class StepUpdateView(ProductionRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    """
    Handles the update view for the Step model, incorporating role-based access, audit
    trail logging, and resetting of statuses as required within the update operation.

    This class is used to modify instances of the Step model while enforcing production
    role requirements, tracking changes through audit trails, and resetting related
    statuses upon updates. It also defines a custom success URL for post-update redirection.

    Attributes:
        model (Step): The model associated with this view.
        form_class (StepForm): The form class used for handling Step model updates.
        template_name (str): The template file used to render the update form.
    """
    model = Step
    form_class = StepForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return f"/production/unit-operations/{self.object.unit_operation.pk}/manage/?view=active"


# =========================================================================
# 4. PARAMETER VIEWS
# =========================================================================
class ParameterStructureView(ProductionRoleRequiredMixin, TemplateView):
    """
    Handles the display of parameters associated with a specific step in a production process.

    This view is responsible for retrieving and organizing data regarding parameters
    and their statuses (active or archived) for a specific step. It also provides
    context variables required for rendering the page, including user group information
    and parameter counts.

    Attributes:
        template_name (str): The path to the template used to render the parameter
            list view.
    """
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


        user_group = None
        if self.request.user.is_authenticated and self.request.user.groups.exists():
            user_group = self.request.user.groups.all()[0].name

        context.update({
            'step': step,
            'unit': step.unit_operation,
            'process': step.unit_operation.process,
            'parameters': parameters,
            'view_mode': view_mode,
            'count_active': count_active,
            'count_archived': count_archived,
            'user_group': user_group,
            'form': context.get('form') or ParameterForm()
        })
        return context


class ParameterAddView(ProductionRoleRequiredMixin, View):
    """
    Handles the addition of a new parameter to a specific step in a production process.

    This view allows users to add parameters to a given step in the production workflow.
    It validates the parameter form, assigns a sequential order to the new parameter, and
    saves it while associating it with the step and user performing the action. Upon
    successful creation, a success message is displayed, and the user is redirected to
    the updated parameters list for the step. Errors during validation or saving are
    handled and appropriate error messages are shown.

    Attributes:
        model_name (str): A description of the model name utilized in the process,

    """
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


class ParameterDeleteView(ProductionRoleRequiredMixin, GenericDeleteView):
    """
    View for deleting a Parameter instance with additional processing.

    This class provides a mechanism to delete a Parameter instance from the production
    workflow, including tasks such as updating the order of active and archived
    parameters after deletion and displaying appropriate user messages. It is designed
    to be used in production settings where ordering and status of parameters are
    critical to system functionality.

    Attributes:
        model (Parameter): The model associated with this view.
    """
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


class ParameterRestoreView(ProductionRoleRequiredMixin, View):
    """
    Handles the restoration of archived parameters for a specific step in the application's production process.

    This view is responsible for restoring a previously archived parameter, updating its order,
    and ensuring the orders of other archived parameters are adjusted accordingly. The process
    is performed within a database transaction to maintain data consistency. Finally, it redirects
    to the archived parameters view for the related step.

    Attributes:
        None
    """
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


class ParameterReorderView(ProductionRoleRequiredMixin, View):
    """
    Handles reordering of parameters within a production step.

    Allows the user to reorder parameters in a production step, either moving
    them up or down the list. Restrictions apply if the associated process
    structure is locked or has a specific status.

    Attributes:
        model (type): The `Parameter` model being manipulated.
    """
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


class ParameterDetailView(ProductionRoleRequiredMixin, EntityDetailView):
    """
    Handles displaying the details of a Parameter entity.

    This class extends the functionality of `EntityDetailView` to provide a detailed view
    of Parameter entities. It incorporates authorization checks and customizes the dynamic
    actions available in the context based on the status of related processes. It ensures
    the appropriate dynamic actions are filtered based on specific conditions, such as
    the process status and entity associations.

    Attributes:
        model (Model): The model the view operates upon. In this case, it is the `Parameter` model.
        template_name (str): The name of the template used for rendering the detail view.
    """
    model = Parameter
    template_name = 'generic/generic_detail.html'

    def get_context_data(self, **kwargs):
        if not hasattr(self.model, 'get_authorized_actions'):
            self.model.get_authorized_actions = lambda instance, user: []

        context = super().get_context_data(**kwargs)

        param = context.get('object')

        if param and param.step and param.step.unit_operation and param.step.unit_operation.process and 'dynamic_actions' in context:
            process_status = param.step.unit_operation.process.status
            if process_status in ['VALIDATED', 'PENDING']:
                context['dynamic_actions'] = [
                    action for action in context['dynamic_actions']
                    if action.get('label') != 'Edit Record'
                ]

        return context


class ParameterUpdateView(ProductionRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    """
    Class for handling parameter updates in the production workflow.

    This class extends multiple mixins to provide functionality such as
    role-based access control, audit trail management, and status reset
    capabilities. It leverages Django's UpdateView to handle updating
    instances of the Parameter model using a form. A specific success URL
    is defined to redirect after the parameter is successfully updated.

    Attributes:
        model: The model being updated, which is Parameter.
        form_class: The form used to update the Parameter model.
        template_name (str): Path to the template used for rendering the form.
    """
    model = Parameter
    form_class = ParameterForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return f"/production/steps/{self.object.step.pk}/parameters/?view=active"

# =========================================================================
# 5. SAMPLE VIEWS
# =========================================================================
class SampleStructureView(ProductionRoleRequiredMixin, TemplateView):
    """
    A view for displaying and managing a list of samples for a specific step in a production process.

    This view is used to show active or archived samples associated with a specific step
    in a production process. The view also provides context information related to the
    step, unit operation, associated process, and the user's group information if available.

    Attributes:
        template_name (str): The path to the template used for rendering the view.
    """
    template_name = 'production/sample_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        step = get_object_or_404(Step, pk=self.kwargs['step_pk'])
        view_mode = self.request.GET.get('view', 'active')

        if view_mode == 'archived':
            samples = Sample.objects.filter(step=step, is_active=False).order_by('created_at')
        else:
            samples = Sample.objects.filter(step=step, is_active=True).order_by('created_at')

        count_active = Sample.objects.filter(step=step, is_active=True).count()
        count_archived = Sample.objects.filter(step=step, is_active=False).count()

        user_group = None
        if self.request.user.is_authenticated and self.request.user.groups.exists():
            user_group = self.request.user.groups.all()[0].name

        context.update({
            'step': step,
            'unit': step.unit_operation,
            'process': step.unit_operation.process,
            'samples': samples,
            'view_mode': view_mode,
            'count_active': count_active,
            'count_archived': count_archived,
            'user_group': user_group,
            'form': context.get('form') or SampleForm()
        })
        return context


class SampleAddView(ProductionRoleRequiredMixin, View):
    """
    Handles the addition of samples associated with a specific step in the production workflow.

    This view facilitates creating and saving a sample linked to a production step. It processes
    a POST request containing form data for a new sample. Upon successful validation and saving,
    a success message is displayed, otherwise error messages are shown. Once processed, the user
    is redirected back to the sample listing of the relevant step.

    Attributes:
        None
    """
    def post(self, request, step_pk):
        step = get_object_or_404(Step, pk=step_pk)
        view_mode = request.GET.get('view', 'active')

        form = SampleForm(request.POST)
        form.instance.step = step

        if form.is_valid():
            try:
                sample = form.save(commit=False)
                sample.created_by = request.user
                sample.updated_by = request.user
                sample.save()
                messages.success(request, f"Sample '{sample.name or ''}' successfully added.")
            except Exception as e:
                messages.error(request, f"Error saving sample: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"[{field.upper()}] {error}")

        return redirect(f"/production/steps/{step.pk}/samples/?view={view_mode}")


class SampleDeleteView(ProductionRoleRequiredMixin, GenericDeleteView):
    """
    Handles the deletion of a sample within a production workflow.

    This class ensures that only users with the required production role can delete
    a sample. Upon successful deletion, it redirects the user to the appropriate
    active samples view of the corresponding step. If deletion fails, a relevant
    error message is displayed, and the process is aborted.

    Attributes:
        model (Sample): Specifies the model associated with this view.
    """
    model = Sample

    def get_success_url(self):
        return f"/production/steps/{self.object.step.pk}/samples/?view=active"

    def form_valid(self, form):
        success_url = self.get_success_url()
        try:
            self.object.delete(user=self.request.user)
            messages.warning(self.request, f"Sample archived.")
        except Exception as e:
            messages.error(self.request, f"Action denied: {str(e)}")
        return HttpResponseRedirect(success_url)


class SampleRestoreView(ProductionRoleRequiredMixin, View):
    """
    Handles the restoration of archived samples in the production system.

    Provides functionality to restore a sample to its active state and handle any
    errors encountered during the restore process. This view enforces role-based
    access control, allowing only users with the "Production Role" to perform the
    operation.

    Attributes:
        None
    """
    def post(self, request, pk):
        sample = get_object_or_404(Sample, pk=pk)
        step_pk = sample.step.pk
        try:
            sample.restore()
            messages.success(request, f"Sample restored successfully.")
        except Exception as e:
            messages.error(request, f"Action denied: {str(e)}")
        return redirect(f"/production/steps/{step_pk}/samples/?view=archived")


class SampleDetailView(ProductionRoleRequiredMixin, EntityDetailView):
    """
    View for displaying detailed information about a Sample.

    This view is responsible for rendering the detailed information of a `Sample`
    object. It ensures that only authorized users can access the view and modifies
    the context data to remove specific dynamic actions based on the status of the
    associated process.

    Attributes:
        model (type): The model associated with this view.
        template_name (str): The template used for rendering the detailed view.
    """
    model = Sample
    template_name = 'generic/generic_detail.html'

    def get_context_data(self, **kwargs):
        if not hasattr(self.model, 'get_authorized_actions'):
            self.model.get_authorized_actions = lambda instance, user: []

        context = super().get_context_data(**kwargs)
        sample = context.get('object')

        if sample and sample.step and sample.step.unit_operation and sample.step.unit_operation.process and 'dynamic_actions' in context:
            process_status = sample.step.unit_operation.process.status
            if process_status in ['VALIDATED', 'PENDING']:
                context['dynamic_actions'] = [
                    action for action in context['dynamic_actions']
                    if action.get('label') != 'Edit Record'
                ]

        return context


class SampleUpdateView(ProductionRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    """
    View for updating a Sample instance.

    This view is responsible for managing the update of a `Sample` object. It ensures proper
    permissions and audit tracking by utilizing several mixins. The view also manages
    the status reset functionality for the updated `Sample`, and uses a form to perform
    validations on the input data during the update process.

    Attributes:
        model (Model): The model class associated with this view. Represents the `Sample` model.
        form_class (Form): The form class used for handling and validating input data.
        template_name (str): The path to the template used for rendering the update view.
    """
    model = Sample
    form_class = SampleForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return f"/production/steps/{self.object.step.pk}/samples/?view=active"


# =========================================================================
# 6. ANALYSIS VIEWS
# =========================================================================
class AnalysisStructureView(ProductionRoleRequiredMixin, TemplateView):
    """
    Represents a view for analyzing the structure of a sample within a production
    process.

    This class is responsible for retrieving context data required to display the
    analysis information related to a specific sample. It supports switching
    between active and archived analyses and includes additional metadata for
    rendering the context in a template. The view is restricted to users with
    specific production roles.

    Attributes:
        template_name (str): The name of the template used for rendering the
            view.
    """
    template_name = 'production/analysis_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sample = get_object_or_404(Sample, pk=self.kwargs['sample_pk'])
        view_mode = self.request.GET.get('view', 'active')

        if view_mode == 'archived':
            analyses = Analysis.objects.filter(sample=sample, is_active=False).order_by('-deleted_at')
        else:
            analyses = Analysis.objects.filter(sample=sample, is_active=True).order_by('created_at')

        count_active = Analysis.objects.filter(sample=sample, is_active=True).count()
        count_archived = Analysis.objects.filter(sample=sample, is_active=False).count()

        user_group = None
        if self.request.user.is_authenticated and self.request.user.groups.exists():
            user_group = self.request.user.groups.all()[0].name

        context.update({
            'sample': sample,
            'step': sample.step,
            'unit': sample.step.unit_operation,
            'process': sample.step.unit_operation.process,
            'analyses': analyses,
            'view_mode': view_mode,
            'count_active': count_active,
            'count_archived': count_archived,
            'user_group': user_group,
            'form': context.get('form') or AnalysisForm()
        })
        return context


class AnalysisAddView(ProductionRoleRequiredMixin, View):
    """Handles the addition of an analysis for a given sample.

    This view is responsible for processing a POST request to add a new analysis
    associated with a specific sample. It validates form data, handles errors, and
    saves the analysis instance to the database if valid. The user is redirected
    to the analysis list page upon completion. User messages indicate success or
    failure of the operation.

    Attributes:
        None
    """
    def post(self, request, sample_pk):
        sample = get_object_or_404(Sample, pk=sample_pk)
        view_mode = request.GET.get('view', 'active')

        form = AnalysisForm(request.POST)
        form.instance.sample = sample

        if form.is_valid():
            try:
                analysis = form.save(commit=False)
                analysis.created_by = request.user
                analysis.updated_by = request.user
                analysis.save()

                messages.success(request, f"Analysis '{analysis.analysis_name}' successfully added.")
            except Exception as e:
                messages.error(request, f"Error saving analysis: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"[{field.upper()}] {error}")

        return redirect(f"/production/samples/{sample.pk}/analyses/?view={view_mode}")


class AnalysisDeleteView(ProductionRoleRequiredMixin, GenericDeleteView):
    """
    Handles the deletion of analysis objects within a production context.

    This view ensures that only users with appropriate production roles can delete
    analysis objects. Upon successful deletion, the user is redirected to an
    active analyses view of the associated sample. If deletion fails, the user is
    presented with an appropriate error message.

    Attributes:
        model (Model): The model associated with the view, specifying the type of
            object this view will handle (Analysis).
    """
    model = Analysis

    def get_success_url(self):
        return f"/production/samples/{self.object.sample.pk}/analyses/?view=active"

    def form_valid(self, form):
        success_url = self.get_success_url()
        try:
            self.object.delete(user=self.request.user)
            messages.warning(self.request, f"Analysis '{self.object.analysis_name}' archived.")
        except Exception as e:
            messages.error(self.request, f"Action denied: {str(e)}")
        return HttpResponseRedirect(success_url)


class AnalysisRestoreView(ProductionRoleRequiredMixin, View):
    """
    Handles the restoration of archived analyses within the production system.

    This view enables authorized users to restore previously archived analyses.
    Upon successful restoration, users are redirected to the analyses page of
    the corresponding sample. It ensures error handling to provide feedback
    in case the restoration fails.

    Methods:
        post: Processes the restoration request for a specified analysis.

    Attributes:
        None
    """
    def post(self, request, pk):
        analysis = get_object_or_404(Analysis, pk=pk)
        sample_pk = analysis.sample.pk
        try:
            analysis.restore()
            messages.success(request, f"Analysis '{analysis.analysis_name}' restored successfully.")
        except Exception as e:
            messages.error(request, f"Action denied: {str(e)}")
        return redirect(f"/production/samples/{sample_pk}/analyses/?view=archived")


class AnalysisDetailView(ProductionRoleRequiredMixin, EntityDetailView):
    """
    Provides a detailed view for the Analysis model, ensuring that only users with the necessary
    production role permissions can access it.

    This class is designed to render a detailed page for an Analysis object using a generic
    template. It customizes the context data to dynamically update actionable user interface
    elements based on the state of related objects, such as the Status of the associated process.

    Attributes:
        model (Model): Specifies the Analysis model as the target for detail view functionality.
        template_name (str): Path to the HTML template used to render the detail view.
    """
    model = Analysis
    template_name = 'generic/generic_detail.html'

    def get_context_data(self, **kwargs):
        if not hasattr(self.model, 'get_authorized_actions'):
            self.model.get_authorized_actions = lambda instance, user: []

        context = super().get_context_data(**kwargs)
        analysis = context.get('object')

        if analysis and analysis.sample and analysis.sample.step and analysis.sample.step.unit_operation and analysis.sample.step.unit_operation.process and 'dynamic_actions' in context:
            process_status = analysis.sample.step.unit_operation.process.status
            if process_status in ['VALIDATED', 'PENDING']:
                context['dynamic_actions'] = [
                    action for action in context['dynamic_actions']
                    if action.get('label') != 'Edit Record'
                ]

        return context


class AnalysisUpdateView(ProductionRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    """View class for updating Analysis objects.

    This class is used to handle the update functionality for Analysis objects.
    It enforces specific production roles, maintains an audit trail of changes, and
    resets statuses as needed.

    This view utilizes a specified form class to render and process the update
    form and provides a custom template for this purpose. Additionally, it
    defines a success URL that redirects to the list of active analyses for
    the associated sample upon successful update.

    Attributes:
        model (Type[Model]): The model that the view will operate on, in this
            case, the `Analysis` model.
        form_class (Type[ModelForm]): The form class used for rendering and processing
            the update form.
        template_name (str): The path to the template used to render the update form.
    """
    model = Analysis
    form_class = AnalysisForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return f"/production/samples/{self.object.sample.pk}/analyses/?view=active"
