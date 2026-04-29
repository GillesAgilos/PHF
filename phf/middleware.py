from django.shortcuts import redirect
from django.conf import settings
from django.urls import resolve


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        current_url_name = resolve(request.path_info).url_name

        exempt_urls = [
            'login',
            'admin:login',
        ]

        if not request.user.is_authenticated and current_url_name not in exempt_urls:
            return redirect(settings.LOGIN_URL)

        return self.get_response(request)