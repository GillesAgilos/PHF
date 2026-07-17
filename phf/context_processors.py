from django.conf import settings

def export_env_name(request):
    return {
        'ENV_NAME': getattr(settings, 'ENV_NAME', 'prod')
    }