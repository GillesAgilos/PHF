from django.urls import path
from . import views

app_name = 'referential'

urlpatterns = [
    # ==========================================
    # CLIENTS
    # ==========================================
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('clients/add/', views.ClientCreateView.as_view(), name='client_add'),
    path('clients/<uuid:pk>/edit/', views.ClientUpdateView.as_view(), name='client_edit'),
    path('clients/<uuid:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),
    path('clients/<uuid:pk>/restore/', views.ClientRestoreView.as_view(), name='client_restore'),
    # New: Validation and History
    path('clients/<uuid:pk>/validate/', views.ClientValidateView.as_view(), name='client_validate'),
    path('clients/<uuid:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('clients/<uuid:pk>/reject/', views.ClientRejectView.as_view(), name='client_reject'),

    # ==========================================
    # PROJECT VIEWS
    # ==========================================
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/add/', views.ProjectCreateView.as_view(), name='project_add'),
    path('projects/<uuid:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('projects/<uuid:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    path('projects/<uuid:pk>/restore/', views.ProjectRestoreView.as_view(), name='project_restore'),
    path('projects/<uuid:pk>/validate/', views.ProjectValidateView.as_view(), name='project_validate'),
    path('projects/<uuid:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projects/<uuid:pk>/reject/', views.ProjectRejectView.as_view(), name='project_reject'),

    # ==========================================
    # MOLECULE TYPES VIEWS
    # ==========================================
    path('molecules/', views.MoleculeTypeListView.as_view(), name='moleculetype_list'),
    path('molecules/add/', views.MoleculeTypeCreateView.as_view(), name='moleculetype_add'),
    path('molecules/<uuid:pk>/edit/', views.MoleculeTypeUpdateView.as_view(), name='moleculetype_edit'),
    path('molecules/<uuid:pk>/delete/', views.MoleculeTypeDeleteView.as_view(), name='moleculetype_delete'),
    path('molecules/<uuid:pk>/restore/', views.MoleculeTypeRestoreView.as_view(), name='moleculetype_restore'),
    path('molecules/<uuid:pk>/validate/', views.MoleculeTypeValidateView.as_view(), name='moleculetype_validate'),
    path('molecules/<uuid:pk>/', views.MoleculeTypeDetailView.as_view(), name='moleculetype_detail'),
    path('molecules/<uuid:pk>/reject/', views.MoleculeTypeRejectView.as_view(), name='moleculetype_reject'),

    # ==========================================
    # ANALYTICAL METHODS
    # ==========================================
    path('analytical-methods/', views.AnalyticalMethodListView.as_view(), name='analyticalmethod_list'),
    path('analytical-methods/add/', views.AnalyticalMethodCreateView.as_view(), name='analyticalmethod_add'),
    path('analytical-methods/<uuid:pk>/edit/', views.AnalyticalMethodUpdateView.as_view(),
         name='analyticalmethod_edit'),
    path('analytical-methods/<uuid:pk>/delete/', views.AnalyticalMethodDeleteView.as_view(),
         name='analyticalmethod_delete'),
    path('analytical-methods/<uuid:pk>/restore/', views.AnalyticalMethodRestoreView.as_view(),
         name='analyticalmethod_restore'),
    path('analytical-methods/<uuid:pk>/validate/', views.AnalyticalMethodValidateView.as_view(),
         name='analyticalmethod_validate'),
    path('analytical-methods/<uuid:pk>/', views.AnalyticalMethodDetailView.as_view(), name='analyticalmethod_detail'),
    path('analytical-methods/<uuid:pk>/reject/', views.AnalyticalMethodRejectView.as_view(),
         name='analyticalmethod_reject'),

    # ==========================================
    # GLOBAL UNIT OPERATIONS (CATALOG)
    # ==========================================
    path('global-units/', views.GlobalUnitOperationListView.as_view(),
         name='globalunitoperation_list'),
    path('global-units/add/', views.GlobalUnitOperationCreateView.as_view(),
         name='globalunitoperation_add'),
    path('global-units/<uuid:pk>/edit/', views.GlobalUnitOperationUpdateView.as_view(),
         name='globalunitoperation_edit'),
    path('global-units/<uuid:pk>/delete/', views.GlobalUnitOperationDeleteView.as_view(),
         name='globalunitoperation_delete'),
    path('global-units/<uuid:pk>/restore/', views.GlobalUnitOperationRestoreView.as_view(),
         name='globalunitoperation_restore'),
    path('global-units/<uuid:pk>/validate/', views.GlobalUnitOperationValidateView.as_view(),
         name='globalunitoperation_validate'),
    path('global-units/<uuid:pk>/', views.GlobalUnitOperationDetailView.as_view(),
         name='globalunitoperation_detail'),
    path('global-units/<uuid:pk>/reject/', views.GlobalUnitOperationRejectView.as_view(),
         name='globalunitoperation_reject'),
]
