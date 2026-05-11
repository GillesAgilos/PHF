from django.urls import path
from . import views

app_name = 'execution'

urlpatterns = [
    # Batch CRUD
    path('batches/', views.BatchListView.as_view(), name='batch_list'),
    path('batches/create/', views.BatchCreateView.as_view(), name='batch_create'),
    path('batches/<uuid:pk>/update/', views.BatchUpdateView.as_view(), name='batch_update'),
    path('batches/<uuid:pk>/delete/', views.BatchDeleteView.as_view(), name='batch_delete'),

    # Parameter Results CRUD
    path('parameter-results/', views.ParameterResultListView.as_view(), name='parameter_result_list'),
    path('parameter-results/create/', views.ParameterResultCreateView.as_view(), name='parameter_result_create'),
    path('parameter-results/<uuid:pk>/update/', views.ParameterResultUpdateView.as_view(), name='parameter_result_update'),
    path('parameter-results/<uuid:pk>/delete/', views.ParameterResultDeleteView.as_view(), name='parameter_result_delete'),

    # Sample Results CRUD
    path('sample-results/', views.SampleResultListView.as_view(), name='sample_result_list'),
    path('sample-results/create/', views.SampleResultCreateView.as_view(), name='sample_result_create'),
    path('sample-results/<uuid:pk>/update/', views.SampleResultUpdateView.as_view(), name='sample_result_update'),
    path('sample-results/<uuid:pk>/delete/', views.SampleResultDeleteView.as_view(), name='sample_result_delete'),
]