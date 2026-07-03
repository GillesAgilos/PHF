from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Prefetch, Max
from django.http import JsonResponse
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
    """View for displaying a list of batches.

    This class-based view is responsible for rendering a list of batches in a
    web application. It supports search functionality and provides contextual
    data such as counts of batches in various statuses. It also customizes the
    queryset used for retrieving batches to optimize related data fetching.

    Attributes:
        model (type): The model associated with this view, representing the
            data structure for batches.
        template_name (str): The template name used to render the batch list.
        context_object_name (str): The name of the context variable that will
            hold the list of batches in the template.
        search_fields (list): A list of fields to allow searching batches,
            specifically project names and process codes.
    """
    model = Batch
    template_name = 'batch/batch_list.html'
    context_object_name = 'batches'
    search_fields = ['name', 'project__code', 'project__client__name', 'project__client__code', 'process__code']

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related('project', 'process').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['view_mode'] = self.request.GET.get('view', 'draft') or 'draft'

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
    """
    Handles batch creation functionality through a web interface.

    This class-based view integrates mixins to enforce role-based access control
    and audit trail logging. It is designed to streamline the creation of batch
    instances using a provided form. It renders a predefined template for
    input collection and redirects users to the batch list view upon
    successful creation.

    Attributes:
        model (type): The model associated with this view, in this case, Batch.
        form_class (type): The form utilized to handle user inputs for creating
            a Batch instance.
        template_name (str): The path to the HTML template used to render
            the form for batch creation.
        success_url (type): A reverse-resolved URL where users are redirected
            after successfully creating a Batch instance.
    """
    model = Batch
    form_class = BatchForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('batch:batch_list')


class BatchUpdateView(BatchRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    """
    View for updating an existing batch.

    This class provides functionality to update an existing batch record through
    a form interface. It inherits from several mixins to ensure role-based access
    control, audit trail management, and status resetting as part of the update
    process. Additionally, it uses Django's UpdateView to handle the form rendering
    and submission.

    Attributes:
        model (Model): The model class associated with this view, which is `Batch`.
        form_class (Form): The form class used in this view, which is `BatchForm`.
        template_name (str): The path to the template file used to render the form.
        success_url (str): The URL path to which users are redirected upon
            successful form submission, pointing to the batch list view.
    """
    model = Batch
    form_class = BatchForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('batch:batch_list')


class BatchDeleteView(BatchRoleRequiredMixin, GenericDeleteView):
    """
    View for managing the deletion of batch instances.

    This class provides functionality to delete instances of the `Batch` model.
    It ensures that only users with the appropriate roles can perform this
    action by inheriting permissions from `BatchRoleRequiredMixin`. The class
    redirects to a predefined success URL upon successful deletion.

    Attributes:
        model: The model class that this view operates on. Set to `Batch`.
        success_url: The URL to redirect to after a successful deletion.
            This is lazily evaluated and set to the `batch_list` URL.
    """
    model = Batch
    success_url = reverse_lazy('batch:batch_list')


class BatchRestoreView(BatchRoleRequiredMixin, GenericRestoreView):
    """Handles the restoration of deleted batches.

    This class is responsible for providing functionality to restore
    deleted batch objects. It extends the permissions and views of
    `BatchRoleRequiredMixin` and `GenericRestoreView` to ensure proper
    access control and restore mechanics.

    Attributes:
        model: The model associated with the view, in this case, `Batch`.
        redirect_url (str): The URL to redirect to after successfully
            restoring a batch.
    """
    model = Batch
    redirect_url = 'batch:batch_list'


class BatchDetailView(BatchRoleRequiredMixin, EntityDetailView):
    """
    Handles the detailed view and context manipulation for Batch objects.

    This class provides a detailed view functionality for Batch objects and integrates
    dynamic actions based on the user's group membership, the batch's status, and other
    contextual conditions.

    Attributes:
        model (type): The model associated with this view. Represents the Batch class.
    """
    model = Batch

    def get_context_data(self, **kwargs):
        if not hasattr(self.model, 'get_authorized_actions'):
            self.model.get_authorized_actions = lambda instance, user: []

        context = super().get_context_data(**kwargs)
        batch = context.get('object') or self.get_object()

        user_groups = self.request.user.groups.values_list('name',
                                                           flat=True) if self.request.user.is_authenticated else []

        if batch and 'dynamic_actions' in context:
            if 'Data_Custodian' in user_groups:
                context['dynamic_actions'] = [
                    action for action in context['dynamic_actions']
                    if action.get('label') != 'Edit Record'
                ]

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
    """
    Handles batch validation functionality.

    This class is responsible for managing the validation of batches. It inherits
    from `BatchRoleRequiredMixin` and `EntityValidateView` to ensure proper role
    permissions and validation functionality. The class provides an endpoint for
    validating a batch by an authorized user and redirects to appropriate views
    based on the action outcome.

    Attributes:
        model (type): The model class associated with the view, which is `Batch`.
        redirect_url (str): The URL to redirect to after validation success.
    """
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
    """
    Handles the rejection of Batch entities with specific role requirements.

    This class is responsible for managing the rejection process for `Batch`
    objects. It enforces specific role requirements through the
    `BatchRoleRequiredMixin` and utilizes the `EntityRejectView` functionality
    to streamline the rejection process. It also provides a configurable
    redirection URL upon successful rejection.

    Attributes:
        model (type): The model class associated with the view, which is `Batch`.
        redirect_url (str): The URL to redirect to after the rejection process
            is completed, set to 'batch:batch_list'.
    """
    model = Batch
    redirect_url = 'batch:batch_list'


class BatchLogbookView(BatchRoleRequiredMixin, DetailView):
    """
    View for displaying the logbook of a batch, including detailed process and analysis
    information.

    This view generates a detailed logbook representation of a batch, providing a hierarchical
    structure of unit operations, steps, parameters, and analyses. It calculates and includes
    results for parameters and analyses associated with the batch, giving an organized view
    to users with access rights.

    Attributes:
        model (Batch): The model associated with this view, representing the batch data.
        template_name (str): The name of the template used for rendering the batch logbook.
        context_object_name (str): The context variable name for the batch object passed to the template.
    """
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
    """
    Manages the view for listing parameter results with search and filter capabilities.

    This class provides functionality to display a list of parameter results
    based on search queries, filtering by status or activity, and ordering.
    It enhances the standard Django ListView by adding custom queryset filtering
    and context data for displaying various counts and user information.

    Attributes:
        model (type): The model associated with the view (ParameterResult).
        template_name (str): The path to the template used to render the view.
        context_object_name (str): The context variable name to use for the list of parameter results.
        search_fields (list of str): Fields of the model that can be searched using a query string.
    """
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
    """
    Represents a view for creating a ParameterResult instance.

    This class is used to handle the creation of a new ParameterResult object using
    a form. It specifies the model, form class, and template to use for rendering the
    view. Additionally, it enforces role-based access control and audit trail logging
    mechanisms.

    Attributes:
        model (ParameterResult): The model class associated with this view.
        form_class (ParameterResultForm): The form class used for creating an instance
            of the model.
        template_name (str): The path to the template used to render the view.
    """
    model = ParameterResult
    form_class = ParameterResultForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class ParameterResultUpdateView(BatchRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    """View for updating a ParameterResult instance.

    This class-based view is used to update a `ParameterResult` instance using
    a form. It inherits from multiple mixins to include additional functionality
    such as handling role-based access, maintaining an audit trail, and resetting
    status upon updates. The form and template are specified for rendering the
    update view.

    Attributes:
        model (ParameterResult): The model being updated by the view.
        form_class (ParameterResultForm): The form class used to handle
            updates for `ParameterResult`.
        template_name (str): The path to the template used for rendering
            the update view.
    """
    model = ParameterResult
    form_class = ParameterResultForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class ParameterResultDeleteView(BatchRoleRequiredMixin, GenericDeleteView):
    """
    Handles the deletion of a ParameterResult object with role-based access control.

    This view inherits from BatchRoleRequiredMixin to enforce role-based security
    and GenericDeleteView to provide the deletion functionality. It is designed
    to delete ParameterResult objects and redirect to a success URL based on the
    related batch's primary key after deletion.

    Attributes:
        model (ParameterResult): The model that the view operates on, representing
            the ParameterResult object to be deleted.
    """
    model = ParameterResult

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class ParameterResultRestoreView(BatchRoleRequiredMixin, GenericRestoreView):
    """
    Handles the restoration of ParameterResult objects within a batch context.

    This class defines functionality for restoring a ParameterResult object
    and redirecting to the batch logbook page. Requires appropriate role-based
    authentication through BatchRoleRequiredMixin.

    Attributes:
        model (ParameterResult): The model associated with this view, used
            for restoring specific instances.
    """
    model = ParameterResult

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.restore()
        return redirect('batch:batch_logbook', pk=obj.batch.pk)


class ParameterResultDetailView(BatchRoleRequiredMixin, EntityDetailView):
    """
    Manages the details view for `ParameterResult` model by handling dynamic actions
    based on user roles and the object's status.

    This view customizes the context data to include dynamic actions, such as
    'Validate', 'Reject', and 'Edit Record', depending on the status of the `ParameterResult`
    object and the roles of the currently authenticated user. It extends from
    `BatchRoleRequiredMixin` and `EntityDetailView` with additional logic tailored to
    handle the `ParameterResult` model.

    Attributes:
        model (ParameterResult): The model associated with the detail view, which is
            used to fetch and display detailed information about a specific object.
    """
    model = ParameterResult

    def get_context_data(self, **kwargs):
        if not hasattr(self.model, 'get_authorized_actions'):
            self.model.get_authorized_actions = lambda instance, user: []

        context = super().get_context_data(**kwargs)
        result = context.get('object') or self.get_object()
        user_groups = self.request.user.groups.values_list('name',
                                                           flat=True) if self.request.user.is_authenticated else []

        if result and 'dynamic_actions' in context:
            context['dynamic_actions'] = [
                action for action in context['dynamic_actions']
                if action.get('label') not in ['Validate', 'Reject', 'Edit Record']
            ]

            if result.status != 'VALIDATED':
                context['dynamic_actions'].append({
                    'label': 'Edit Record',
                    'url': reverse('batch:parameter_result_edit', kwargs={'pk': result.pk}),
                    'class': 'btn-outline-primary',
                    'icon': 'bi bi-pencil'
                })

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
    """
    Handles the validation of a ParameterResult instance and redirects upon completion.

    This class is designed to ensure entities of type ParameterResult are validated
    by a user with the proper permissions. Upon successful validation, the user is
    redirected to a specific batch logbook page.

    Attributes:
        model (type): The model associated with this view, set to ParameterResult.
    """
    model = ParameterResult

    def post(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        obj.validate_entity(user=request.user)
        return redirect('batch:batch_logbook', pk=obj.batch.pk)


class ParameterResultRejectView(BatchRoleRequiredMixin, EntityRejectView):
    """
    Handles the rejection of parameter results within a batch context.

    This view facilitates rejecting a parameter result with a provided reason and updates its status.
    It ensures the user has the appropriate role to perform this action.

    Attributes:
        model (type): Specifies the model associated with the view, `ParameterResult`.
    """
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
    """
    Manages the display and filtering of a list of analysis results.

    This class provides functionality for rendering a list view of analysis results
    with customizable filtering options based on the user's query parameters.
    It handles different view modes (active, archived, rejected, draft)
    and allows searching through specific fields. Additionally, it calculates
    context information such as counts for various status categories
    and includes it in the response.

    Attributes:
        model (Model): The model associated with this view.
            For this class, it is set to `AnalysisResult`.
        template_name (str): The path to the template used for rendering the view.
        context_object_name (str): The name of the context variable that will
            contain the queryset in the template.
        search_fields (list of str): A list of model fields to be searched when
            filtering by query.
    """
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
    """
    View for creating an `AnalysisResult` instance.

    This class-based view is responsible for handling the creation of a new
    `AnalysisResult` instance. It uses a form for user input, ensures that the
    user has the necessary permissions, and records audit trails for actions
    performed. The view redirects to a success URL upon successful creation.

    Attributes:
        model (Model): The model associated with this view, which is `AnalysisResult`.
        form_class (Form): The form used for creating a new `AnalysisResult` instance.
        template_name (str): The template used to render the view.
    """
    model = AnalysisResult
    form_class = AnalysisResultForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class AnalysisResultUpdateView(BatchRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    """
    Handles the update functionality for AnalysisResult objects by rendering a form view.

    This class provides a user interface for updating existing AnalysisResult objects
    through a form. It integrates several mixins to add specific functionality, such as
    role-based access control, audit trail logging, and status resetting during the update process.
    It also defines the specific model, form, and template used for rendering the update view.

    Attributes:
        model (AnalysisResult): The model class associated with this view, representing
            an analysis result that will be updated.
        form_class (AnalysisResultForm): The form class used for rendering and validating
            the fields required for updating an AnalysisResult object.
        template_name (str): The path to the template file used for rendering the form view.
    """
    model = AnalysisResult
    form_class = AnalysisResultForm
    template_name = 'generic/generic_form.html'

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class AnalysisResultDeleteView(BatchRoleRequiredMixin, GenericDeleteView):
    """
    Handles the deletion of an AnalysisResult object.

    Specialized view for facilitating the deletion operation of AnalysisResult
    objects while enforcing batch-based role restrictions. This class ensures
    users with certain permissions tied to specific batches can execute the delete
    operation. After successful deletion, redirection to the associated batch logbook
    view is executed to provide relevant context.

    Attributes:
        model (type): The model class targeted for deletion, which is AnalysisResult.
    """
    model = AnalysisResult

    def get_success_url(self):
        return reverse('batch:batch_logbook', kwargs={'pk': self.object.batch.pk})


class AnalysisResultRestoreView(BatchRoleRequiredMixin, GenericRestoreView):
    """
    Handles the restoration of an AnalysisResult instance.

    This class provides functionality for restoring an instance of the
    AnalysisResult model. It integrates role-based access control and uses
    a POST request to handle the restoration operation. Upon successful
    restoration, it redirects to the appropriate batch logbook page.

    Attributes:
        model (AnalysisResult): Specifies the model class associated with
            this view.
    """
    model = AnalysisResult

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.restore()
        return redirect('batch:batch_logbook', pk=obj.batch.pk)


class AnalysisResultDetailView(BatchRoleRequiredMixin, EntityDetailView):
    """Class for managing the detailed view of an analysis result.

    Provides functionality for rendering the detail view of an analysis result
    and dynamically adjusting the context based on user roles, actions, and the
    status of the analysis result.

    Attributes:
        model (Model): The model associated with the detailed view. In this case,
            it is the `AnalysisResult` model.
    """
    model = AnalysisResult

    def get_context_data(self, **kwargs):
        if not hasattr(self.model, 'get_authorized_actions'):
            self.model.get_authorized_actions = lambda instance, user: []

        context = super().get_context_data(**kwargs)
        result = context.get('object') or self.get_object()
        user_groups = self.request.user.groups.values_list('name',
                                                           flat=True) if self.request.user.is_authenticated else []

        if result and 'dynamic_actions' in context:
            context['dynamic_actions'] = [
                action for action in context['dynamic_actions']
                if action.get('label') not in ['Validate', 'Reject', 'Edit Record']
            ]

            if result.status != 'VALIDATED':
                context['dynamic_actions'].append({
                    'label': 'Edit Record',
                    'url': reverse('batch:analysis_result_edit', kwargs={'pk': result.pk}),
                    'class': 'btn-outline-primary',
                    'icon': 'bi bi-pencil'
                })

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
    """
    Handles the validation of analysis results within the context of batch processing.

    This class provides functionality to validate analysis results tied to a specific
    batch entity. It ensures that only authorized users with the required roles can
    initiate the validation process. Upon successful validation, the user is redirected
    to the associated batch logbook page.

    Attributes:
        model (Model): The model associated with the analysis result, specifically
            `AnalysisResult`.
    """
    model = AnalysisResult

    def post(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        obj.validate_entity(user=request.user)
        return redirect('batch:batch_logbook', pk=obj.batch.pk)


class AnalysisResultRejectView(BatchRoleRequiredMixin, EntityRejectView):
    """
    Handles the rejection of analysis results.

    This class provides functionality to reject an analysis result with a specified
    reason. It ensures that only users with the appropriate role can perform this
    action. Upon rejection, the analysis result's status is updated, the rejection
    reason is stored, and it is logged appropriately in the associated batch
    logbook.

    Attributes:
        model (type): The model class associated with this view, representing the
            analysis result.
    """
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


@login_required
def get_next_iteration(request):
    project_id = request.GET.get('project_id')
    if not project_id:
        return JsonResponse({'next_iteration': 1})

    max_iter = Batch.objects.filter(
        project_id=project_id,
        is_active=True
    ).aggregate(Max('iteration_number'))['iteration_number__max']

    next_iter = (max_iter or 0) + 1
    return JsonResponse({'next_iteration': next_iter})
