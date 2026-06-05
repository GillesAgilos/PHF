from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView
from phf.utils import (
    EntityValidateView,
    EntityRejectView,
    GenericDeleteView,
    GenericRestoreView,
    EntityDetailView
)


class ReferentialRoleRequiredMixin(LoginRequiredMixin):
    """
    Global security Mixin for the Referential application.
    Rights Matrix:
    - System_Admin       : Full Access (Bypass)
    - Data_Steward       : Read-Only (List/Detail) + Write (Create/Update/Delete/Restore)
    - QA_Representative  : Read-Only (List/Detail) + Decision (Validate/Reject)
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        # Superuser bypass: System_Admin
        if request.user.is_superuser or request.user.groups.filter(name='System_Admin').exists():
            return super().dispatch(request, *args, **kwargs)

        # Extract user groups synchronized from Entra ID
        user_groups = request.user.groups.values_list('name', flat=True)
        current_view = self

        # READ-ONLY VIEWS (
        is_read_only_view = isinstance(current_view, ListView) or isinstance(current_view, EntityDetailView)
        if is_read_only_view and ('Data_Steward' in user_groups or 'QA_Representative' in user_groups):
            return super().dispatch(request, *args, **kwargs)

        if 'Data_Steward' in user_groups:
            is_steward_action = (
                    isinstance(current_view, CreateView) or
                    isinstance(current_view, UpdateView) or
                    isinstance(current_view, GenericDeleteView) or
                    isinstance(current_view, GenericRestoreView)
            )
            if is_steward_action:
                return super().dispatch(request, *args, **kwargs)

            raise PermissionDenied("Data Stewards are not allowed to validate or reject referential data.")

        if 'QA_Representative' in user_groups:
            is_qa_action = isinstance(current_view, EntityValidateView) or isinstance(current_view, EntityRejectView)
            if is_qa_action:
                return super().dispatch(request, *args, **kwargs)

            raise PermissionDenied("QA Representatives are not allowed to create or modify referential data.")

        raise PermissionDenied("Access denied. You do not have the required role to access this module.")