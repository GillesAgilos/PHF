import uuid
from django.db import models
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views import View
from django.views.generic import DeleteView, ListView
from simple_history.models import HistoricalRecords
from django.urls import reverse_lazy
from datetime import datetime, date


# ==========================================
# BASE MODEL
# ==========================================

class BaseModel(models.Model):
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
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_created")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_updated")
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_deleted")

    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True

    def validate_entity(self, user=None):
        self.status = self.Status.VALIDATED
        if user: self.updated_by = user
        self.save()

    def delete(self, user=None, *args, **kwargs):
        self.is_active = False
        self.deleted_at = timezone.now()
        if user: self.deleted_by = user
        self.save()

    def restore(self):
        self.is_active = True
        self.status = self.Status.DRAFT
        self.deleted_at = None
        self.deleted_by = None
        self.save()

    def clean(self):
        super().clean()
        for field in self._meta.fields:
            if isinstance(field, models.ForeignKey):
                related_obj = getattr(self, field.name)
                if related_obj:
                    if hasattr(related_obj, 'status') and related_obj.status != self.Status.VALIDATED:
                        raise ValidationError({field.name: f"Selected item ({related_obj}) must be validated."})
                    if hasattr(related_obj, 'is_active') and not related_obj.is_active:
                        raise ValidationError({field.name: f"Selected item ({related_obj}) is archived."})

    def save(self, *args, **kwargs):
        if self.is_active: self.full_clean()
        super().save(*args, **kwargs)

    def get_admin_url(self, action):
        """Helper to dynamically generate urls matching model name"""
        model_name = self._meta.model_name
        return reverse_lazy(f'referential:{model_name}_{action}', kwargs={'pk': self.pk})

    @property
    def validate_url(self):
        return self.get_admin_url('validate')

    @property
    def reject_url(self):
        return self.get_admin_url('reject')

    @property
    def edit_url(self):
        return self.get_admin_url('edit')

    class Meta:
        abstract = True


# ==========================================
# MIXIN VIEWS
# ==========================================

class AuditTrailMixin:
    """ created by and updated by insert automatically + security check """
    def form_valid(self, form):
        if form.instance.pk:
            current_obj = self.model.objects.filter(pk=form.instance.pk).first()

            if current_obj and not current_obj.is_active:
                messages.error(self.request,
                               f"Action denied: This {self.model._meta.verbose_name} is archived. Restore it first.")
                return redirect(current_obj.get_admin_url('detail'))

        if not form.instance.pk:
            form.instance.created_by = self.request.user

        form.instance.updated_by = self.request.user

        return super().form_valid(form)

class StatusResetMixin:
    """set status to draft if changed is made to the object"""
    def form_valid(self, form):
        if form.instance.pk and form.has_changed():
            form.instance.status = BaseModel.Status.DRAFT
            messages.info(self.request, "Changes detected: Status reset to 'To validate'.")
        return super().form_valid(form)


class FilterStateMixin:
    """manage filter on archived or active objects, search options on list"""
    search_fields = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('q')
        if search_query:
            search_filter = Q()
            for field in self.search_fields:
                search_filter |= Q(**{f"{field}__icontains": search_query})
            queryset = queryset.filter(search_filter)

        view_mode = self.request.GET.get('view', 'pending') or 'pending'

        if view_mode == 'archived':
            return queryset.filter(is_active=False).order_by('-deleted_at')
        elif view_mode == 'active':
            return queryset.filter(is_active=True, status='VALIDATED').order_by('name')
        else:
            return queryset.filter(is_active=True).exclude(status='VALIDATED').order_by('-updated_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        view_mode = self.request.GET.get('view', 'pending') or 'pending'
        search_query = self.request.GET.get('q', '')

        context['view_mode'] = view_mode
        context['search_query'] = search_query

        base_qs = self.model.objects.all()
        if search_query:
            search_filter = Q()
            for field in self.search_fields:
                search_filter |= Q(**{f"{field}__icontains": search_query})
            base_qs = base_qs.filter(search_filter)

        context['count_pending'] = base_qs.filter(is_active=True).exclude(status='VALIDATED').count()
        context['count_active'] = base_qs.filter(is_active=True, status='VALIDATED').count()
        context['count_archived'] = base_qs.filter(is_active=False).count()

        return context

# ==========================================
# GENERIC VIEWS
# ==========================================

class GenericDeleteView(DeleteView):
    template_name = 'generic/generic_confirm_delete.html'
    def form_valid(self, form):
        self.object.delete(user=self.request.user)
        messages.success(self.request, f"{self.model.__name__} archived.")
        return HttpResponseRedirect(self.get_success_url())


class GenericRestoreView(View):
    model = None
    redirect_url = None

    def get_object(self):
        # Récupère l'objet via l'ID passé dans l'URL
        return get_object_or_404(self.model, pk=self.kwargs.get('pk'))

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        try:
            obj.restore()
            messages.success(request, f"{obj._meta.verbose_name.capitalize()} restored successfully.")
        except ValidationError as e:
            error_msg = "Cannot restore: "

            if hasattr(e, 'message_dict') and 'client' in e.message_dict:
                error_msg += "The linked client is currently archived. You must restore the client before this project."
            else:
                error_msg += str(e.messages[0] if hasattr(e, 'messages') else e)

            messages.error(request, error_msg)
        except Exception as e:
            messages.error(request, f"An error occurred during restoration: {str(e)}")

        return redirect(self.redirect_url)

class EntityValidateView(View):
    """
    Generic view to handle the validation workflow.
    Expects a post request to trigger the validate_entity method.
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
    generic view to reject an entity
    """
    model = None
    redirect_url = None

    def post(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)

        if not obj.is_active:
            messages.error(request, "Cannot reject an archived entity.")
        else:
            obj.status = obj.Status.REJECTED
            obj.updated_by = request.user
            obj.save()
            messages.warning(request, f"{self.model.__name__} '{obj}' has been rejected.")

        return redirect(self.redirect_url)


class EntityDetailView(AuditTrailMixin, ListView):
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

        # audit logic
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

        # display settings
        custom_fields = getattr(self, 'display_fields_list', None)
        excluded_fields = []
        display_fields = []

        # define where and how to get fields
        iterable_fields = custom_fields if custom_fields else [f.name for f in self.obj._meta.fields]

        for field_name in iterable_fields:
            if not custom_fields and field_name in excluded_fields:
                continue

            try:
                f = self.model._meta.get_field(field_name)
                if f.choices:
                    display_method = f"get_{field_name}_display"
                    value = getattr(self.obj, display_method)()
                else:
                    value = getattr(self.obj, field_name)

                # transform in string only if not a date, int boo, ...
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