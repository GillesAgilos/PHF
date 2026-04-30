from django.shortcuts import redirect
from django.conf import settings
from django.urls import resolve


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # we get full path (namespace:name)
        resolver_match = resolve(request.path_info)
        current_url = f"{resolver_match.namespace}:{resolver_match.url_name}" if resolver_match.namespace else resolver_match.url_name

        exempt_urls = [
            'login',
            'admin:login',
            'django_auth_adfs:login',
            'django_auth_adfs:callback',
            'django_auth_adfs:logout',
        ]

        if not request.user.is_authenticated and current_url not in exempt_urls:
            return redirect(settings.LOGIN_URL)

        return self.get_response(request)