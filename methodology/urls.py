from django.urls import path
from . import views

app_name = 'methodology'

urlpatterns = [
    # Processes
    path('processes/', views.ProcessListView.as_view(), name='process_list'),
    path('processes/add/', views.ProcessCreateView.as_view(), name='process_add'),
    path('processes/<uuid:pk>/edit/', views.ProcessUpdateView.as_view(), name='process_edit'),

    # Unit Operations
    path('unit-ops/', views.UnitOperationListView.as_view(), name='unit_op_list'),
    path('unit-ops/add/', views.UnitOperationCreateView.as_view(), name='unit_op_add'),
    path('unit-ops/<uuid:pk>/edit/', views.UnitOperationUpdateView.as_view(), name='unit_op_edit'),

    # Sequences
    path('sequences/', views.SequenceListView.as_view(), name='sequence_list'),
    path('sequences/add/', views.SequenceCreateView.as_view(), name='sequence_add'),

    # Parameters
    path('parameters/', views.ParameterListView.as_view(), name='parameter_list'),
    path('parameters/add/', views.ParameterCreateView.as_view(), name='parameter_add'),

    # Generic Restore for methodology
    path('restore/<str:model_nm>/<uuid:pk>/', views.MethodologyRestoreView.as_view(), name='restore'),
]