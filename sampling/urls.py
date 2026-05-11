from django.urls import path
from . import views

app_name = 'sampling'

urlpatterns = [
    # Analytical Methods
    path('methods/', views.MethodListView.as_view(), name='method_list'),
    path('methods/add/', views.MethodCreateView.as_view(), name='method_add'),

    # Sampling Plans
    path('plans/', views.PlanListView.as_view(), name='plan_list'),
    path('plans/add/', views.PlanCreateView.as_view(), name='plan_add'),
    path('plans/<uuid:pk>/manage/', views.PlanManageView.as_view(), name='plan_manage'),

    # Samples (Entries within a plan)
    path('plans/<uuid:plan_pk>/sample/add/', views.SampleCreateView.as_view(), name='sample_add'),
    path('sample/<uuid:pk>/delete/', views.SampleDeleteView.as_view(), name='sample_delete'),
]