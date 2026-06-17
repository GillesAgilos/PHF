import uuid
from datetime import date, datetime
from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import DeleteView, ListView
from simple_history.models import HistoricalRecords

# =========================================================================
# BASE MODEL FOR SIMPLE ENTITIES
# =========================================================================

class BaseModel(models.Model):
    """
    BaseModel serves as an abstract base class, providing essential fields and functionality
    for all models inheriting from it. It includes status tracking, soft-deletion mechanics,
    audit fields for tracking creation and modification metadata, and utility methods for
    common operations such as validation, restoration, and field-level cleaning.

    Attributes:
        unique_id (UUIDField): The universally unique identifier for the model instance,
            serving as the primary key.
        status (CharField): Represents the current lifecycle status of the object, with choices
            including 'DRAFT', 'VALIDATED', and 'REJECTED'.
        created_at (DateTimeField): The timestamp indicating when the record was created.
        created_by (ForeignKey): A reference to the user who created the record. Can be null or blank.
        updated_at (DateTimeField): The timestamp indicating the last time the record was updated.
        updated_by (ForeignKey): A reference to the user who last updated the record. Can be null or blank.
        is_active (BooleanField): Indicates whether the record is currently active or soft-deleted.
        deleted_at (DateTimeField): The timestamp of when the record was soft-deleted. Can be null or blank.
        deleted_by (ForeignKey): A reference to the user who soft-deleted the record. Can be null or blank.
        history (HistoricalRecords): Historical tracking of changes made to the model instance.
        rejection_reason (TextField): A reason provided for why the record was rejected.
    """
    unique_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'To validate'
        VALIDATED = 'VALIDATED', 'Validated'
        REJECTED = 'REJECTED', 'Rejected'

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT,
        help_text="Object must be validated first to be used in other relations."
    )

    # Audit & Soft Delete
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="%(class)s_created")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="%(class)s_updated")
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="%(class)s_deleted")
    history = HistoricalRecords(inherit=True)
    rejection_reason = models.TextField(null=True, blank=True, help_text="Reason why this was rejected")
    _change_reason = None

    class Meta:
        abstract = True

    def validate_entity(self, user=None):
        self.status = 'VALIDATED'
        if user: self.updated_by = user
        self.save()

    def delete(self, user=None, *args, **kwargs):
        self.is_active = False
        self.deleted_at = timezone.now()
        if user: self.deleted_by = user
        self.save()

    def restore(self):
        self.is_active = True
        self.status = getattr(self.Status, 'DRAFT', 'DRAFT')
        self.deleted_at = None
        self.deleted_by = None
        self.save()

    def clean(self):
        super().clean()
        for field in self._meta.fields:
            if isinstance(field, models.ForeignKey):
                related_obj = getattr(self, field.name)
                if related_obj:
                    if hasattr(related_obj, 'status') and related_obj.status != 'VALIDATED':
                        raise ValidationError({field.name: f"Selected item ({related_obj}) must be validated."})
                    if hasattr(related_obj, 'is_active') and not related_obj.is_active:
                        raise ValidationError({field.name: f"Selected item ({related_obj}) is archived."})

    def save(self, *args, **kwargs):
        if self.is_active: self.full_clean()
        super().save(*args, **kwargs)

    def get_admin_url(self, action):
        model_name = self._meta.model_name
        app_label = self._meta.app_label
        return reverse_lazy(f'{app_label}:{model_name}_{action}', kwargs={'pk': self.pk})

    @property
    def validate_url(self):
        return self.get_admin_url('validate')

    @property
    def reject_url(self):
        return self.get_admin_url('reject')

    @property
    def edit_url(self):
        return self.get_admin_url('edit')

    @property
    def _history_change_reason(self):
        return self._change_reason

    @_history_change_reason.setter
    def _history_change_reason(self, value):
        self._change_reason = value

    def get_authorized_actions(self, user):
        """
        Determines the set of actions a user is authorized to perform on the object, based
        on their authentication status, group memberships, and the current state of the
        object. Different roles such as "System_Admin", "Data_Steward", and "QA_Representative"
        have varying levels of permissions and can perform specific actions.

        Args:
            user (User): The user for whom the authorized actions are being determined.

        Returns:
            list: A list of dictionaries, where each dictionary represents a specific action the
            user is authorized to perform. Each dictionary contains the following keys:
                - 'label' (str): The display label for the action.
                - 'url' (str): The URL endpoint where the action is performed.
                - 'class' (str): The CSS classes to style the action.
                - 'icon' (str): The icon class for visual representation.
                - 'method' (str): The HTTP method to use when performing the action.
        """
        actions = []
        if not user.is_authenticated:
            return actions

        # Resolve role with a fallback if a Super User has no groups assigned
        is_admin = user.is_superuser
        user_group = None

        if user.groups.exists():
            user_group = user.groups.all()[0].name
            if user_group == "System_Admin":
                is_admin = True

        #  ARCHIVAL CASE (Record is inactive/soft-deleted)
        if not self.is_active:
            if is_admin or user_group == "Data_Steward":
                actions.append({
                    'label': 'Restore Record',
                    'url': reverse(f"{self._meta.app_label}:{self._meta.model_name}_restore", kwargs={'pk': self.pk}),
                    'class': 'btn-info shadow-sm',
                    'icon': 'bi-arrow-counterclockwise',
                    'method': 'POST'
                })
            return actions

        # DATA STEWARD RIGHTS (Always allowed to edit active records)
        if is_admin or user_group == "Data_Steward":
            actions.append({
                'label': 'Edit Record',
                'url': self.edit_url,
                'class': 'btn-outline-primary',
                'icon': 'bi-pencil',
                'method': 'GET'
            })

        # QA REPRESENTATIVE RIGHTS (Allowed to Validate/Reject when status is DRAFT)
        if is_admin or user_group == "QA_Representative":
            if self.status == 'DRAFT':
                actions.append({
                    'label': 'Validate',
                    'url': self.validate_url,
                    'class': 'btn-success shadow-sm px-4',
                    'icon': 'bi-check-circle',
                    'method': 'POST'
                })
                actions.append({
                    'label': 'Reject',
                    'url': self.reject_url,
                    'class': 'btn-outline-danger shadow-sm',
                    'icon': 'bi-x-circle',
                    'method': 'MODAL',
                    'target': '#rejectModal'
                })

        return actions

# =========================================================================
# BASE COMPONENT MODEL (FOR DEPENDENT MODELS)
# =========================================================================

class BaseComponentEntity(models.Model):
    """
    Represents a base model entity with common fields and functionalities for tracking
    creation, updates, soft-deletion, and historical records.

    This class serves as an abstract model to be extended by other models that require
    basic entity tracking features such as audit fields for creation, modification,
    soft-deletion handling, and historical record keeping. It ensures data consistency
    through the clean method and enforces validation constraints tied to parent entities.

    Attributes:
        unique_id (UUIDField): A unique identifier for the entity, automatically
            generated as the primary key.
        created_at (DateTimeField): Timestamp when the entity was created, set
            automatically at creation.
        created_by (ForeignKey): The user who created the entity. Can be null or
            blank, with a reference to the AUTH_USER_MODEL.
        updated_at (DateTimeField): Timestamp when the entity was last updated,
            set automatically on every update.
        updated_by (ForeignKey): The user who last updated the entity. Can be
            null or blank, with a reference to the AUTH_USER_MODEL.
        is_active (BooleanField): Indicates whether the entity is active. Used
            for soft deletion. Defaults to True.
        deleted_at (DateTimeField): Timestamp when the entity was soft-deleted. Can
            be null or blank.
        deleted_by (ForeignKey): The user who soft-deleted the entity. Can be null
            or blank, with a reference to the AUTH_USER_MODEL.
        history (HistoricalRecords): Historical record management for tracking
            changes to the entity over time.
    """
    unique_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="%(class)s_created")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="%(class)s_updated")
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="%(class)s_deleted")

    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True

    def delete(self, user=None, *args, **kwargs):
        self.is_active = False
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save()

    def restore(self):
        self.is_active = True
        self.deleted_at = None
        self.deleted_by = None
        self.save()

    def get_parent_entity(self):
        raise NotImplementedError("You must implement get_parent_entity() to return the parent object.")

    def clean(self):
        super().clean()
        parent = self.get_parent_entity()

        if parent:
            if hasattr(parent, 'status') and parent.status == 'VALIDATED':
                raise ValidationError(
                    f"Cannot modify this element because the parent template '{parent}' is already validated and locked.")
            if hasattr(parent, 'is_active') and not parent.is_active:
                raise ValidationError(f"Cannot modify this element because the parent template '{parent}' is archived.")

    def save(self, *args, **kwargs):
        if self.is_active:
            self.full_clean()

        super().save(*args, **kwargs)


# =========================================================================
# MIXIN VIEWS
# =========================================================================

class ProcessLockRequiredMixin:
    """
    Mixin to enforce access restrictions on locked process-related views.

    This mixin checks whether the requested object or process is in a locked state
    (i.e., 'VALIDATED' or 'PENDING') and denies the action when appropriate. It can
    be used to protect views where operations should not be allowed on locked
    processes, units, or steps.

    Attributes:
        None
    """
    def dispatch(self, request, *args, **kwargs):
        obj = None
        if hasattr(self, 'get_object'):
            try:
                obj = self.get_object()
            except Exception:
                pass

        process = None
        if obj:
            if obj.__class__.__name__ == 'Process':
                process = obj
            elif hasattr(obj, 'process'):
                process = obj.process
            elif hasattr(obj, 'unit_operation'):
                process = obj.unit_operation.process
            elif hasattr(obj, 'step'):
                process = obj.step.unit_operation.process

        if not process:
            if 'process_pk' in self.kwargs:
                from django.apps import apps
                ProcessModel = apps.get_model('production', 'Process')
                process = get_object_or_404(ProcessModel, pk=self.kwargs['process_pk'])
            elif 'unit_pk' in self.kwargs:
                from django.apps import apps
                UnitModel = apps.get_model('production', 'UnitOperation')
                unit = get_object_or_404(UnitModel, pk=self.kwargs['unit_pk'])
                process = unit.process
            elif 'step_pk' in self.kwargs:
                from django.apps import apps
                StepModel = apps.get_model('production', 'Step')
                step = get_object_or_404(StepModel, pk=self.kwargs['step_pk'])
                process = step.unit_operation.process

        if process and process.status in ['VALIDATED', 'PENDING']:
            messages.error(
                request,
                f"Action denied: The process chart '{process.name}' is locked ({process.get_status_display()})."
            )

            if obj and obj.__class__.__name__ == 'Process':
                return redirect('production:process_list')
            elif 'step_pk' in self.kwargs or (obj and hasattr(obj, 'step')):
                step_pk = self.kwargs.get('step_pk') or obj.step.pk
                return redirect(f"{reverse('production:parameter_list', kwargs={'step_pk': step_pk})}?view=active")
            elif 'unit_pk' in self.kwargs or (obj and hasattr(obj, 'unit_operation')):
                unit_pk = self.kwargs.get('unit_pk') or obj.unit_operation.pk
                return redirect(f"{reverse('production:step_list', kwargs={'unit_pk': unit_pk})}?view=active")
            else:
                process_pk = process.pk
                return redirect(
                    f"{reverse('production:unitoperation_list', kwargs={'process_pk': process_pk})}?view=active")

        return super().dispatch(request, *args, **kwargs)


class AuditTrailMixin:
    """
    A mixin to enhance form handling with audit trail functionality for Django admin interfaces.

    This mixin is designed to add audit trail capabilities, providing features such as restriction
    of actions on inactive or archived objects, tracking changes with justifications, and recording
    user actions for object creation and updates. It is intended for use in a Django admin
    context, where forms are required to manage model instances effectively.

    Attributes:
        model (type): The associated Django model class that this mixin interacts with.
        request (type): The current HttpRequest object containing metadata about the
            request, typically passed in during runtime operations.
    """
    def form_valid(self, form):
        if form.instance.pk:
            current_obj = self.model.objects.filter(pk=form.instance.pk).first()
            if current_obj and not current_obj.is_active:
                messages.error(self.request,
                               f"Action denied: This {self.model._meta.verbose_name} is archived. Restore it first.")
                return redirect(current_obj.get_admin_url('detail'))

        if form.instance.pk and form.has_changed():
            reason = form.cleaned_data.get('change_justification')
            if reason:
                form.instance._change_reason = reason

        if form.instance._state.adding:
            form.instance.created_by = self.request.user

        form.instance.updated_by = self.request.user

        return super().form_valid(form)


class StatusResetMixin:
    """
    Mixin to reset the status of a model instance upon form validation if changes
    are detected.

    This mixin modifies the behavior of the form's validation process to reset the
    `status` field of the corresponding model instance to 'DRAFT' when changes have
    been made to the form inputs. It is intended to be used in scenarios where the
    status of a model instance must reflect any ongoing edits or updates.

    Methods:
        form_valid: Overrides the default form validation behavior to include logic
            for resetting the `status` field if necessary.
    """
    def form_valid(self, form):
        if form.instance.pk and form.has_changed():
            form.instance.status = 'DRAFT'
            messages.info(self.request, "Changes detected: Status reset to 'Draft / To validate'.")
        return super().form_valid(form)


class FilterStateMixin:
    """
    A mixin class for filtering querysets and managing context data in list views.

    This class provides functionalities to filter querysets based on search terms
    and view modes, such as active, archived, and rejected items. It also adds
    additional context data to the views, such as counts for different statuses
    and URL filters for pagination or query parameters navigation.

    Attributes:
        search_fields (list of str): Fields to be used for search filtering.
        paginate_by (int): The number of items to be displayed per page.
    """
    search_fields = ['name']
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('q')

        if search_query:
            search_filter = Q()
            for field in self.search_fields:
                search_filter |= Q(**{f"{field}__icontains": search_query})
            queryset = queryset.filter(search_filter)

        is_process_model = hasattr(self.model, 'Status') and hasattr(self.model.Status, 'PENDING')
        default_view = 'active'
        view_mode = self.request.GET.get('view', default_view) or default_view

        if view_mode == 'archived':
            return queryset.filter(is_active=False).order_by('-deleted_at')
        elif view_mode == 'active':
            return queryset.filter(is_active=True, status='VALIDATED').order_by(
                'name' if not is_process_model else 'code')
        elif view_mode == 'rejected':
            return queryset.filter(is_active=True, status='REJECTED').order_by('-updated_at')
        elif view_mode == 'draft' and is_process_model:
            return queryset.filter(is_active=True, status='DRAFT').order_by('-updated_at')
        else:
            if is_process_model:
                return queryset.filter(is_active=True, status='PENDING').order_by('-updated_at')
            return queryset.filter(is_active=True, status='DRAFT').order_by('-updated_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_process_model = hasattr(self.model, 'Status') and hasattr(self.model.Status, 'PENDING')

        default_view = 'active'
        view_mode = self.request.GET.get('view', default_view) or default_view

        context['view_mode'] = view_mode
        context['search_query'] = self.request.GET.get('q', '')

        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['url_filters'] = query_params.urlencode()

        base_qs = self.model.objects.all()
        if context['search_query']:
            search_filter = Q()
            for field in self.search_fields:
                search_filter |= Q(**{f"{field}__icontains": context['search_query']})
            base_qs = base_qs.filter(search_filter)

        if is_process_model:
            context['count_draft'] = base_qs.filter(is_active=True, status='DRAFT').count()
            context['count_pending'] = base_qs.filter(is_active=True, status='PENDING').count()
        else:
            context['count_draft'] = 0
            context['count_pending'] = base_qs.filter(is_active=True, status='DRAFT').count()

        context['count_rejected'] = base_qs.filter(is_active=True, status='REJECTED').count()
        context['count_active'] = base_qs.filter(is_active=True, status='VALIDATED').count()
        context['count_archived'] = base_qs.filter(is_active=False).count()

        return context


# =========================================================================
# GENERIC VIEWS (Delete, Restore, Validate, Reject, Detail)
# =========================================================================

class GenericDeleteView(DeleteView):
    """
    Handles the deletion of objects with a confirmation step and success message.

    This class provides functionality for confirming and processing the deletion of
    objects. It uses a predefined template for the confirmation page and allows
    archiving of objects by associating the deletion action with a user. A success
    message is displayed upon successful deletion.

    Attributes:
        template_name (str): Path to the template used for the confirmation page.
    """
    template_name = 'generic/generic_confirm_delete.html'

    def form_valid(self, form):
        self.object.delete(user=self.request.user)
        messages.success(self.request, f"{self.model.__name__} archived.")
        return HttpResponseRedirect(self.get_success_url())


class GenericRestoreView(View):
    """
    View for handling the restoration of a model instance.

    This class provides functionality to restore a previously deleted or deactivated
    model instance. It retrieves the instance, attempts to restore it using its
    `restore` method, and then redirects the user to a specified URL. Success or
    failure messages are displayed to the user based on the operation's result.

    Attributes:
        model (Model): The model class associated with the view. This attribute
            should be set to specify which model to access for restoration.
        redirect_url (str): The URL to redirect the user to after the restoration
            attempt is complete.
    """
    model = None
    redirect_url = None

    def get_object(self):
        return get_object_or_404(self.model, pk=self.kwargs.get('pk'))

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        try:
            obj.restore()
            messages.success(request, f"{obj._meta.verbose_name.capitalize()} restored successfully.")
        except ValidationError as e:
            error_msg = f"Cannot restore: {str(e.messages[0] if hasattr(e, 'messages') else e)}"
            messages.error(request, error_msg)
        return redirect(self.redirect_url)


class EntityValidateView(View):
    """
    Handles entity validation in a web application.

    This class-based view is used to validate specific entities within a web application.
    It retrieves an object based on the provided primary key, invokes a validation method on
    the object, displays a success message, and redirects to a specified URL.

    Attributes:
        model (type): The model class associated with the entity to be validated.
        redirect_url (str): The URL to which the user is redirected after validation.
    """
    model = None
    redirect_url = None

    def post(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        obj.validate_entity(user=request.user)
        messages.success(request, f"{self.model.__name__} '{obj}' has been validated.")
        return redirect(self.redirect_url)


class EntityRejectView(View):
    """
    Allows rejection of a specific entity instance by handling POST requests.

    The EntityRejectView class enables updating the status of a specific entity
    instance to 'REJECTED' along with a reason provided by the user. This view
    is particularly useful for workflows that support rejecting objects with
    customizable rejection reasons. It also displays appropriate messages to
    the user upon successful or failed operations.

    Attributes:
        model (Type[Model]): The model class that the view handles. It should
            be a subclass of `django.db.models.Model`.
        redirect_url (str): The URL to which the user will be redirected after
            processing the request.
    """
    model = None
    redirect_url = None

    def post(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        reason = request.POST.get('rejection_reason')
        if not reason:
            messages.error(request, "You must provide a reason for rejection.")
            return redirect(self.redirect_url)
        obj.status = 'REJECTED'
        obj.rejection_reason = reason
        obj.updated_by = request.user
        obj.save()
        messages.warning(request, f"{self.model.__name__} rejected: {reason}")
        return redirect(self.redirect_url)


class EntityDetailView(AuditTrailMixin, ListView):
    """
    View class to display detailed information and historical changes of an object.

    This class provides functionality to fetch and display the history of changes
    for an object, including a detailed comparison of its historical states.
    It dynamically generates a user-friendly context used for rendering the
    template, including object details, field changes, and authorized user actions.

    Attributes:
        template_name (str): The path to the template used for rendering the view.
        context_object_name (str): The key under which the queryset will be
            available in the template context.

    """
    template_name = 'generic/generic_detail.html'
    context_object_name = 'history_records'

    def get_queryset(self):
        self.obj = get_object_or_404(self.model, pk=self.kwargs['pk'])
        return self.obj.history.all().order_by('-history_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = self.obj
        context['title'] = f"Details & History: {self.obj}"
        context['model_name'] = self.model._meta.model_name

        context['dynamic_actions'] = self.obj.get_authorized_actions(self.request.user)

        history_list = []
        records = list(context['history_records'])
        for i in range(len(records)):
            new_record = records[i]
            changes = []
            if i < len(records) - 1:
                old_record = records[i + 1]
                delta = new_record.diff_against(old_record)
                for change in delta.changes:
                    ignored = ['updated_at', 'updated_by', 'history_user', 'history_date', 'history_user_id',
                               'updated_by_id']
                    if change.field not in ignored:
                        field_name = change.field
                        old_val, new_val = change.old, change.new
                        lookup_name = field_name[:-3] if field_name.endswith('_id') else field_name
                        try:
                            field_obj = self.model._meta.get_field(lookup_name)
                            if field_obj.is_relation:
                                rel_model = field_obj.related_model
                                old_obj = rel_model.objects.filter(pk=old_val).first() if old_val else None
                                new_obj = rel_model.objects.filter(pk=new_val).first() if new_val else None
                                old_val, new_val = str(old_obj) if old_obj else "None", str(
                                    new_obj) if new_obj else "None"
                                field_name = lookup_name
                        except:
                            pass
                        changes.append({'field': field_name.replace('_', ' ').upper(), 'old': old_val, 'new': new_val})
            history_list.append({'record': new_record, 'changes': changes})
        context['history_list'] = history_list

        display_fields = []
        ignored_display_fields = ['unique_id','status']

        audit_fields_at_the_end = [
            'status',
            'created_at', 'created_by',
            'updated_at', 'updated_by',
            'deleted_at', 'deleted_by',
            'is_active', 'rejection_reason'
        ]

        first_fields = []
        last_fields = []

        for f in self.model._meta.fields:
            if f.name in ignored_display_fields:
                continue
            if f.name in audit_fields_at_the_end:
                last_fields.append(f)
            else:
                first_fields.append(f)

        ordered_fields = first_fields + last_fields

        for f in ordered_fields:
            try:
                field_name = f.name
                if f.choices:
                    value = getattr(self.obj, f"get_{field_name}_display")()
                else:
                    value = getattr(self.obj, field_name)

                if hasattr(value, '__str__') and not isinstance(value, (str, int, bool, datetime, date, type(None))):
                    value = str(value)

                display_fields.append({
                    'label': f.verbose_name.replace('_', ' '),
                    'value': value
                })
            except:
                continue

        context['display_fields'] = display_fields
        return context


# =========================================================================
# BASE ENTITY FORM
# =========================================================================

class BaseEntityForm(forms.ModelForm):
    """
    This class represents a form for managing entity modifications with an optional
    justification field.

    The form extends `forms.ModelForm` to provide additional functionality for tracking
    and validating the reason for modifying an entity. It ensures that modifications
    are accompanied by a descriptive justification when necessary. The form is designed
    to handle cases for both new entity creation and modifications to existing entities.

    Attributes:
        change_justification (forms.CharField): A text field for capturing the reason
            for entity modification. It is optional during creation but required
            when modifying an existing entity.
    """
    change_justification = forms.CharField(
        widget=forms.Textarea(
            attrs={'rows': 2, 'placeholder': 'Why are you modifying this entity?', 'class': 'form-control'}),
        required=False,
        label="Reason for modification"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance._state.adding:
            self.fields.pop('change_justification', None)

    def clean(self):
        cleaned_data = super().clean()
        if self.instance and not self.instance._state.adding and self.has_changed():
            if 'change_justification' not in self.fields:
                self.add_error(None, "Justification field is missing for update operations.")
                return cleaned_data
            justification = cleaned_data.get('change_justification', '').strip()
            if not justification or len(justification) < 5:
                self.add_error('change_justification',
                               "A descriptive reason (min. 5 characters) is required to save modifications.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance._state.adding and 'change_justification' in self.cleaned_data:
            instance._change_reason = self.cleaned_data['change_justification']
        if commit: instance.save()
        return instance
