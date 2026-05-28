from django.urls import path
from . import views

app_name = 'batch'

urlpatterns = [
    # =========================================================================
    # BATCH TARGETS
    # =========================================================================
    path('batches/', views.BatchListView.as_view(), name='batch_list'),
    path('batches/add/', views.BatchCreateView.as_view(), name='batch_add'),
    path('batches/<uuid:pk>/edit/', views.BatchUpdateView.as_view(), name='batch_edit'),
    path('batches/<uuid:pk>/delete/', views.BatchDeleteView.as_view(), name='batch_delete'),
    path('batches/<uuid:pk>/restore/', views.BatchRestoreView.as_view(), name='batch_restore'),
    path('batches/<uuid:pk>/validate/', views.BatchValidateView.as_view(), name='batch_validate'),
    path('batches/<uuid:pk>/reject/', views.BatchRejectView.as_view(), name='batch_reject'),
    path('batches/<uuid:pk>/', views.BatchDetailView.as_view(), name='batch_detail'),

    # NOUVELLE ROUTE LOGBOOK GROUPÉ (OUVERT/FERMÉ + ENCODAGE DIRECT)
    path('batches/<uuid:pk>/logbook/', views.BatchLogbookView.as_view(), name='batch_logbook'),

    # =========================================================================
    # PARAMETER RESULTS URLs
    # =========================================================================
    path('parameters-results/', views.ParameterResultListView.as_view(), name='parameterresult_list'),
    path('parameters-results/add/', views.ParameterResultCreateView.as_view(), name='parameterresult_add'),
    path('parameters-results/<uuid:pk>/edit/', views.ParameterResultUpdateView.as_view(), name='parameterresult_edit'),
    path('parameters-results/<uuid:pk>/delete/', views.ParameterResultDeleteView.as_view(), name='parameterresult_delete'),
    path('parameters-results/<uuid:pk>/restore/', views.ParameterResultRestoreView.as_view(), name='parameterresult_restore'),
    path('parameters-results/<uuid:pk>/validate/', views.ParameterResultValidateView.as_view(), name='parameterresult_validate'),
    path('parameters-results/<uuid:pk>/reject/', views.ParameterResultRejectView.as_view(), name='parameterresult_reject'),
    path('parameters-results/<uuid:pk>/', views.ParameterResultDetailView.as_view(), name='parameterresult_detail'),

    # =========================================================================
    # SAMPLE RESULTS URLs
    # =========================================================================
    path('samples-results/', views.SampleResultListView.as_view(), name='sampleresult_list'),
    path('samples-results/add/', views.SampleResultCreateView.as_view(), name='sampleresult_add'),
    path('samples-results/<uuid:pk>/edit/', views.SampleResultUpdateView.as_view(), name='sampleresult_edit'),
    path('samples-results/<uuid:pk>/delete/', views.SampleResultDeleteView.as_view(), name='sampleresult_delete'),
    path('samples-results/<uuid:pk>/restore/', views.SampleResultRestoreView.as_view(), name='sampleresult_restore'),
    path('samples-results/<uuid:pk>/validate/', views.SampleResultValidateView.as_view(), name='sampleresult_validate'),
    path('samples-results/<uuid:pk>/reject/', views.SampleResultRejectView.as_view(), name='sampleresult_reject'),
    path('samples-results/<uuid:pk>/', views.SampleResultDetailView.as_view(), name='sampleresult_detail'),
]