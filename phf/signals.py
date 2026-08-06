import os
from django.contrib.auth.models import Group
from django.dispatch import receiver
from django_auth_adfs.signals import post_authenticate


@receiver(post_authenticate)
def map_azure_groups_to_django_permissions(sender, user, claims, **kwargs):
    """
    Maps Azure AD groups to corresponding Django permissions using claims information.

    The function listens to the post_authenticate signal. It maps Azure Active Directory
    user groups provided in the claims to Django's user group objects and sets the user's
    group membership, administrator flags, and active status based on the matched role.
    The user's account is active only when exactly one configured role matches; accounts
    with no matching role or multiple matching roles are deactivated.

    Args:
        sender: The object that sent the signal. Typically the backend handling authentication.
        user: The authenticated Django user instance whose permissions are being updated.
        claims: A dictionary containing claims returned from Azure AD, including group
            memberships.
        **kwargs: Additional keyword arguments passed by the signal.

    """
    azure_groups = claims.get('groups', [])

    mapping_env = {
        'System_Admin': os.getenv('AZURE_GROUP_ADMIN'),
        'Data_Custodian': os.getenv('AZURE_GROUP_CUSTODIAN'),
        'Data_Steward': os.getenv('AZURE_GROUP_STEWARD'),
        'QA_Representative': os.getenv('AZURE_GROUP_QA'),
        'Data_Investigator': os.getenv('AZURE_GROUP_INVESTIGATOR'),
    }

    user.groups.clear()
    user.is_staff = False
    user.is_superuser = False

    matched_roles = []

    for django_group_name, azure_id in mapping_env.items():
        if azure_id and azure_id in azure_groups:
            matched_roles.append(django_group_name)

    if len(matched_roles) == 1:
        django_group_name = matched_roles[0]
        group, _ = Group.objects.get_or_create(name=django_group_name)
        user.groups.add(group)
        user.is_active = True

        if django_group_name == 'System_Admin':
            user.is_staff = True
            user.is_superuser = True
    else:
        user.is_active = False

    user.save()
