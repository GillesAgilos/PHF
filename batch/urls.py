from django.urls import path
from . import views

app_name = 'batch'

urlpatterns = [
    # =========================================================================
    # BATCHES
    # =========================================================================
    path('batches/', views.BatchListView.as_view(), name='batch_list'),
    path('batches/add/', views.BatchCreateView.as_view(), name='batch_add'),
    path('batches/<uuid:pk>/edit/', views.BatchUpdateView.as_view(), name='batch_edit'),
    path('batches/<uuid:pk>/delete/', views.BatchDeleteView.as_view(), name='batch_delete'),
    path('batches/<uuid:pk>/restore/', views.BatchRestoreView.as_view(), name='batch_restore'),
    path('batches/<uuid:pk>/detail/', views.BatchDetailView.as_view(), name='batch_detail'),
    path('batches/<uuid:pk>/validate/', views.BatchValidateView.as_view(), name='batch_validate'),
    path('batches/<uuid:pk>/reject/', views.BatchRejectView.as_view(), name='batch_reject'),
    path('batches/<uuid:pk>/logbook/', views.BatchLogbookView.as_view(), name='batch_logbook'),

    # =========================================================================
    # PARAMETER RESULTS
    # =========================================================================
    path('parameter-results/', views.ParameterResultListView.as_view(), name='parameter_result_list'),
    path('parameter-results/add/', views.ParameterResultCreateView.as_view(), name='parameter_result_add'),
    path('parameter-results/<uuid:pk>/edit/', views.ParameterResultUpdateView.as_view(), name='parameter_result_edit'),
    path('parameter-results/<uuid:pk>/delete/', views.ParameterResultDeleteView.as_view(), name='parameter_result_delete'),
    path('parameter-results/<uuid:pk>/restore/', views.ParameterResultRestoreView.as_view(), name='parameter_result_restore'),
    path('parameter-results/<uuid:pk>/detail/', views.ParameterResultDetailView.as_view(), name='parameter_result_detail'),
    path('parameter-results/<uuid:pk>/validate/', views.ParameterResultValidateView.as_view(), name='parameter_result_validate'),
    path('parameter-results/<uuid:pk>/reject/', views.ParameterResultRejectView.as_view(), name='parameter_result_reject'),

    # =========================================================================
    # ANALYSIS RESULTS
    # =========================================================================
    path('analysis-results/', views.AnalysisResultListView.as_view(), name='analysis_result_list'),
    path('analysis-results/add/', views.AnalysisResultCreateView.as_view(), name='analysis_result_add'),
    path('analysis-results/<uuid:pk>/edit/', views.AnalysisResultUpdateView.as_view(), name='analysis_result_edit'),
    path('analysis-results/<uuid:pk>/delete/', views.AnalysisResultDeleteView.as_view(), name='analysis_result_delete'),
    path('analysis-results/<uuid:pk>/restore/', views.AnalysisResultRestoreView.as_view(), name='analysis_result_restore'),
    path('analysis-results/<uuid:pk>/detail/', views.AnalysisResultDetailView.as_view(), name='analysis_result_detail'),
    path('analysis-results/<uuid:pk>/validate/', views.AnalysisResultValidateView.as_view(), name='analysis_result_validate'),
    path('analysis-results/<uuid:pk>/reject/', views.AnalysisResultRejectView.as_view(), name='analysis_result_reject'),
]