from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    # --- Processes ---
    path('processes/', views.ProcessListView.as_view(), name='process_list'),
    path('processes/add/', views.ProcessCreateView.as_view(), name='process_add'),
    path('processes/<uuid:pk>/edit/', views.ProcessUpdateView.as_view(), name='process_edit'),
    path('processes/<uuid:pk>/delete/', views.ProcessDeleteView.as_view(), name='process_delete'),
    path('processes/<uuid:pk>/restore/', views.ProcessRestoreView.as_view(), name='process_restore'),

    # --- Unit Operations ---
    path('processes/<uuid:process_pk>/units/', views.UnitOperationManageView.as_view(), name='unit_manage'),
    path('processes/<uuid:process_pk>/units/add/', views.UnitOperationCreateView.as_view(), name='unit_add'),
    path('units/<uuid:pk>/delete/', views.UnitOperationDeleteView.as_view(), name='unit_delete'),
    path('units/<uuid:pk>/reorder/<str:direction>/', views.UnitReorderView.as_view(), name='unit_reorder'),

    # --- Steps ---
    path('units/<uuid:unit_pk>/steps/', views.StepManageView.as_view(), name='step_manage'),
    path('units/<uuid:unit_pk>/steps/add/', views.StepCreateView.as_view(), name='step_add'),
    path('steps/<uuid:pk>/reorder/<str:direction>/', views.StepReorderView.as_view(), name='step_reorder'),
    path('steps/<uuid:pk>/delete/', views.StepDeleteView.as_view(), name='step_delete'),

    # --- Parameters ---
    path('steps/<uuid:step_pk>/parameters/', views.ParameterManageView.as_view(), name='parameter_manage'),
    path('steps/<uuid:step_pk>/parameters/add/', views.ParameterCreateView.as_view(), name='parameter_add'),
    path('parameters/<uuid:pk>/reorder/<str:direction>/', views.ParameterReorderView.as_view(),
         name='parameter_reorder'),
    path('parameters/<uuid:pk>/delete/', views.ParameterDeleteView.as_view(), name='parameter_delete'),
]
