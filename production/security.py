from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView
from phf.utils import (
    EntityValidateView,
    EntityRejectView,
    GenericDeleteView,
    GenericRestoreView,
    EntityDetailView,
)


class ProductionRoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin that enforces role-based access control for views in a production environment.

    This mixin extends `LoginRequiredMixin` and adds additional role-based validation for
    users based on their group memberships. It restricts access and certain actions
    based on the roles defined for users, ensuring stricter control over production data handling.

    Attributes:
        None

    Global security Mixin for the Production application.
    Rights Matrix:
    - System_Admin       : Full Access (Bypass)
    - Data_Steward       : Read-Only (List/Detail/Structure) + Write (Create/Update/Delete/Restore)
    - QA_Representative  : Read-Only (List/Detail/Structure) + Decision (Validate/Reject)
    - Data_Investigator  : Read-Only (List/Detail)
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
        view_class_name = current_view.__class__.__name__.lower()
        read_only_roles = {'Data_Steward', 'QA_Representative', 'Data_Investigator'}

        is_read_only_view = isinstance(current_view, (ListView, EntityDetailView, TemplateView))
        if is_read_only_view and any(role in user_groups for role in read_only_roles):
            return super().dispatch(request, *args, **kwargs)


        if 'Data_Steward' in user_groups:
            if isinstance(current_view, EntityValidateView) or isinstance(current_view,
                                                                          EntityRejectView) or 'validate' in view_class_name or 'reject' in view_class_name:
                raise PermissionDenied("Data Stewards are not allowed to validate or reject production data.")

            return super().dispatch(request, *args, **kwargs)

        if 'QA_Representative' in user_groups:
            is_mutation_action = (
                    'create' in view_class_name or
                    'edit' in view_class_name or
                    'update' in view_class_name or
                    'delete' in view_class_name or
                    'restore' in view_class_name or
                    isinstance(current_view, GenericDeleteView) or
                    isinstance(current_view, GenericRestoreView)
            )
            if is_mutation_action:
                raise PermissionDenied("QA Representatives are not allowed to create or modify production data.")

            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied("Access denied. You do not have the required role to access this module.")
