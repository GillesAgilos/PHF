from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from phf.utils import (
    EntityValidateView,
    EntityRejectView,
    GenericDeleteView,
    GenericRestoreView,
    EntityDetailView
)

class BatchRoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin to enforce role-based permissions for accessing views and performing
    specific actions in a Django application.

    This class extends the functionality of `LoginRequiredMixin`, ensuring that
    only authenticated users with appropriate roles can perform actions on views.
    It introduces fine-grained access control based on the user's group membership
    and the type of view being accessed. This mixin supports use cases such as
    read-only views for QA users, action-specific permissions for Data Custodians
    and Data Stewards, and unrestricted access for superusers and System Administrators.

    Attributes:
        None

    Security Mixin for the Batch & Results application.
    Rights Matrix:
    - System_Admin     : Full Access (Bypass)
    - Data_Custodian   : Read-Only on Batch + Write on Parameters/Results logbook
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

        current_model = getattr(current_view, 'model', None)
        current_model_name = getattr(current_model, '__name__', None)
        custodian_logbook_models = {'ParameterResult', 'AnalysisResult'}

        is_read_only_view = isinstance(current_view, ListView) or isinstance(current_view, EntityDetailView) or isinstance(current_view, DetailView)
        if is_read_only_view:
            if 'Data_Custodian' in user_groups or 'Data_Steward' in user_groups or 'QA' in user_groups or 'QA_Representative' in user_groups:
                return super().dispatch(request, *args, **kwargs)

        if 'Data_Custodian' in user_groups:
            if current_model_name in custodian_logbook_models:
                return super().dispatch(request, *args, **kwargs)

            raise PermissionDenied("Data Custodians are only allowed to work on the logbook results, not on batch records.")

        if 'Data_Steward' in user_groups:
            is_steward_action = isinstance(current_view, EntityValidateView) or isinstance(current_view, EntityRejectView)
            if is_steward_action:
                return super().dispatch(request, *args, **kwargs)

            raise PermissionDenied("Data Stewards are restricted to validation and rejection tasks only.")

        if 'QA' in user_groups or 'QA_Representative' in user_groups:
            raise PermissionDenied("QA profiles have read-only access and cannot modify or validate batch data.")

        raise PermissionDenied("Access denied. You do not have the required role to access this module.")
