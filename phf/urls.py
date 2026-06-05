from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('oauth2/', include('django_auth_adfs.urls')),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('referential/', include('referential.urls')),
    path('production/', include('production.urls')),
    path('batch/', include('batch.urls')),
]
