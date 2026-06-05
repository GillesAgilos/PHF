import os
from django.contrib.auth.models import Group
from django.dispatch import receiver
from django_auth_adfs.signals import post_authenticate


@receiver(post_authenticate)
def map_azure_groups_to_django_permissions(sender, user, claims, **kwargs):
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