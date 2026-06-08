from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from phf.utils import (
    EntityValidateView,
    EntityRejectView,
    GenericDeleteView,
    GenericRestoreView,
    EntityDetailView
)

class BatchRoleRequiredMixin(LoginRequiredMixin):
    """
    Security Mixin for the Batch & Results application.
    Rights Matrix:
    - System_Admin     : Full Access (Bypass)
    - Data_Custodian   : Read-Only + Write (Create/Update/Delete/Restore)
    - Data_Steward     : Read-Only + Decision (Validate/Reject)
    - QA               : Read-Only Only (List/Detail)
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        # 1. Superuser bypass: System_Admin
        if request.user.is_superuser or request.user.groups.filter(name='System_Admin').exists():
            return super().dispatch(request, *args, **kwargs)

        user_groups = request.user.groups.values_list('name', flat=True)
        current_view = self

        is_read_only_view = isinstance(current_view, ListView) or isinstance(current_view, EntityDetailView) or isinstance(current_view, DetailView)
        if is_read_only_view:
            if 'Data_Custodian' in user_groups or 'Data_Steward' in user_groups or 'QA' in user_groups or 'QA_Representative' in user_groups:
                return super().dispatch(request, *args, **kwargs)

        if 'Data_Custodian' in user_groups:
            is_custodian_action = (
                    isinstance(current_view, CreateView) or
                    isinstance(current_view, UpdateView) or
                    isinstance(current_view, GenericDeleteView) or
                    isinstance(current_view, GenericRestoreView)
            )
            if is_custodian_action:
                return super().dispatch(request, *args, **kwargs)

            raise PermissionDenied("Data Custodians are not allowed to validate or reject batch data.")

        if 'Data_Steward' in user_groups:
            is_steward_action = isinstance(current_view, EntityValidateView) or isinstance(current_view, EntityRejectView)
            if is_steward_action:
                return super().dispatch(request, *args, **kwargs)

            raise PermissionDenied("Data Stewards are restricted to validation and rejection tasks only.")

        if 'QA' in user_groups or 'QA_Representative' in user_groups:
            raise PermissionDenied("QA profiles have read-only access and cannot modify or validate batch data.")

        raise PermissionDenied("Access denied. You do not have the required role to access this module.")