from django.shortcuts import redirect
from django.conf import settings
from django.urls import resolve


class LoginRequiredMiddleware:
    """
    Middleware that enforces login requirements and redirects users to a login page when
    accessing protected views.

    This middleware intercepts HTTP requests, checks if the user is authenticated,
    and ensures that users attempting to access non-exempt URLs are redirected to
    the login page if not authenticated. Exempt URLs are specified and bypass this
    check, allowing unauthenticated access.

    Attributes:
        get_response (Callable): The next middleware or view in the request response
            cycle, invoked after this middleware processes the request.
    """
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