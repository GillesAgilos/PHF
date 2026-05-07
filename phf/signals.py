import os
from django.contrib.auth.models import Group
from django.dispatch import receiver
from django_auth_adfs.signals import post_authenticate


@receiver(post_authenticate)
def map_azure_groups_to_django_permissions(sender, user, claims, **kwargs):
    # getting groups ids sent by Entra ID
    azure_groups = claims.get('groups', [])

    # loading group IDs from environment variables
    # these variables must be defined in your .env file
    mapping_env = {
        os.getenv('AZURE_GROUP_ADMIN'): 'System_Admin',
        os.getenv('AZURE_GROUP_CUSTODIAN'): 'Data_Custodian',
        os.getenv('AZURE_GROUP_STEWARD'): 'Data_Steward',
        os.getenv('AZURE_GROUP_QA'): 'QA_Representative',
        os.getenv('AZURE_GROUP_INVESTIGATOR'): 'Data_Investigator',
    }

    # clear default rights and groups to ensure a fresh sync at each login
    user.groups.clear()
    user.is_staff = False
    user.is_superuser = False

    # flag to check if the user belongs to at least one authorized group
    user_has_mapped_group = False

    # iterate through mapping to assign Django groups based on Azure IDs
    for azure_id, django_group_name in mapping_env.items():
        if azure_id and azure_id in azure_groups:
            group, _ = Group.objects.get_or_create(name=django_group_name)
            user.groups.add(group)
            user_has_mapped_group = True

            # privilege escalation for System Admin only
            if django_group_name == 'System_Admin':
                user.is_staff = True
                user.is_superuser = True

    # if user is not in a mapped group, account is deactivated for security
    if not user_has_mapped_group:
        user.is_active = False
    else:
        user.is_active = True

    user.save()