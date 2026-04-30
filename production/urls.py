from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    # Batches
    path('batches/', views.BatchListView.as_view(), name='batch_list'),
    path('batches/add/', views.BatchCreateView.as_view(), name='batch_add'),
    path('batches/<uuid:pk>/', views.BatchDetailView.as_view(), name='batch_detail'),

    # Execution
    path('samples/add/', views.SampleCreateView.as_view(), name='sample_add'),
    path('results/add/', views.SampleResultCreateView.as_view(), name='result_add'),

    # Restore
    path('restore/<str:model_nm>/<uuid:pk>/', views.ProductionRestoreView.as_view(), name='restore'),
]