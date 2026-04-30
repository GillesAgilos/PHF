from django.urls import path
from . import views

app_name = 'referential'

urlpatterns = [
    # Clients
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('clients/add/', views.ClientCreateView.as_view(), name='client_add'),
    path('clients/<uuid:pk>/edit/', views.ClientUpdateView.as_view(), name='client_edit'),
    path('clients/<uuid:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),
    path('clients/<uuid:pk>/restore/', views.ClientRestoreView.as_view(), name='client_restore'),

    # Projects
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/add/', views.ProjectCreateView.as_view(), name='project_add'),
    path('projects/<uuid:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('projects/<uuid:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    path('projects/<uuid:pk>/restore/', views.ProjectRestoreView.as_view(), name='project_restore'),
]