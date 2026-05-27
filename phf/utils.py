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


# =========================================================================
# BASE COMPONENT MODEL (FOR DEPENDENT MODELS)
# =========================================================================

class BaseComponentEntity(models.Model):
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
        # Sécurité au niveau de l'ORM : déclenche le full_clean() qui exécutera clean()
        if self.is_active:
            self.full_clean()

        # Le bloc qui forçait le statut du parent à repasser en DRAFT a été supprimé ici
        super().save(*args, **kwargs)


# =========================================================================
# MIXIN VIEWS
# =========================================================================

class ProcessLockRequiredMixin:
    """
    Bloque les requêtes HTTP (POST, GET de modification) si le Process racine
    est verrouillé (VALIDATED ou PENDING). Redirige proprement avec un message d'erreur.
    """

    def dispatch(self, request, *args, **kwargs):
        obj = None
        if hasattr(self, 'get_object'):
            try:
                obj = self.get_object()
            except Exception:
                pass

        process = None
        # 1. Extraction du Process depuis l'objet de la vue
        if obj:
            if obj.__class__.__name__ == 'Process':
                process = obj
            elif hasattr(obj, 'process'):
                process = obj.process
            elif hasattr(obj, 'unit_operation'):
                process = obj.unit_operation.process
            elif hasattr(obj, 'step'):
                process = obj.step.unit_operation.process

        # 2. Extraction du Process depuis les paramètres de l'URL (si ajout)
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

        # 3. Vérification du verrouillage
        if process and process.status in ['VALIDATED', 'PENDING']:
            messages.error(
                request,
                f"Action denied: The process chart '{process.name}' is locked ({process.get_status_display()})."
            )

            # Redirections intelligentes selon le niveau de profondeur de l'action déniée
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
    def form_valid(self, form):
        if form.instance.pk:
            current_obj = self.model.objects.filter(pk=form.instance.pk).first()
            if current_obj and not current_obj.is_active:
                messages.error(self.request,
                               f"Action denied: This {self.model._meta.verbose_name} is archived. Restore it first.")
                return redirect(current_obj.get_admin_url('detail'))

        if form.instance.pk and form.has_changed():
            reason = form.cleaned_data.get('change_justification')
            if reason: form.instance._change_reason = reason

        if not form.instance.pk:
            form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        return super().form_valid(form)


class StatusResetMixin:
    def form_valid(self, form):
        if form.instance.pk and form.has_changed():
            form.instance.status = 'DRAFT'
            messages.info(self.request, "Changes detected: Status reset to 'Draft / To validate'.")
        return super().form_valid(form)


class FilterStateMixin:
    search_fields = ['name']

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
    template_name = 'generic/generic_confirm_delete.html'

    def form_valid(self, form):
        self.object.delete(user=self.request.user)
        messages.success(self.request, f"{self.model.__name__} archived.")
        return HttpResponseRedirect(self.get_success_url())


class GenericRestoreView(View):
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
    model = None
    redirect_url = None

    def post(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        obj.validate_entity(user=request.user)
        messages.success(request, f"{self.model.__name__} '{obj}' has been validated.")
        return redirect(self.redirect_url)


class EntityRejectView(View):
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
        iterable_fields = [f.name for f in self.obj._meta.fields]
        for field_name in iterable_fields:
            try:
                f = self.model._meta.get_field(field_name)
                if f.choices:
                    value = getattr(self.obj, f"get_{field_name}_display")()
                else:
                    value = getattr(self.obj, field_name)
                if hasattr(value, '__str__') and not isinstance(value, (str, int, bool, datetime, date, type(None))):
                    value = str(value)
                display_fields.append({'label': f.verbose_name.replace('_', ' '), 'value': value})
            except:
                continue

        context['display_fields'] = display_fields
        return context


# =========================================================================
# BASE ENTITY FORM
# =========================================================================

class BaseEntityForm(forms.ModelForm):
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
