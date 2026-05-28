from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    # =========================================================================
    # LEVEL 1 : PROCESS TEMPLATES
    # =========================================================================
    path('processes/', views.ProcessListView.as_view(), name='process_list'),
    path('processes/add/', views.ProcessCreateView.as_view(), name='process_add'),
    path('processes/<uuid:pk>/edit/', views.ProcessUpdateView.as_view(), name='process_edit'),
    path('processes/<uuid:pk>/delete/', views.ProcessDeleteView.as_view(), name='process_delete'),
    path('processes/<uuid:pk>/restore/', views.ProcessRestoreView.as_view(), name='process_restore'),
    path('processes/<uuid:pk>/detail/', views.ProcessDetailView.as_view(), name='process_detail'),
    path('processes/<uuid:pk>/submit/', views.ProcessSubmitView.as_view(), name='process_submit'),
    path('processes/<uuid:pk>/validate/', views.ProcessValidateView.as_view(), name='process_validate'),
    path('processes/<uuid:pk>/reject/', views.ProcessRejectView.as_view(), name='process_reject'),
    path('processes/<uuid:pk>/new-version/', views.ProcessCreateNewVersionView.as_view(), name='process_versioning'),

    # =========================================================================
    # LEVEL 2 : UNIT OPERATIONS
    # =========================================================================
    path('processes/<uuid:process_pk>/structure/', views.UnitOperationStructureView.as_view(),
         name='unitoperation_list'),
    path('processes/<uuid:process_pk>/structure/add/', views.UnitOperationAddView.as_view(), name='unitoperation_add'),
    path('unit-operations/<uuid:pk>/edit/', views.UnitOperationUpdateView.as_view(), name='unitoperation_edit'),
    path('unit-operations/<uuid:pk>/delete/', views.UnitOperationDeleteView.as_view(), name='unitoperation_delete'),
    path('unit-operations/<uuid:pk>/restore/', views.UnitOperationRestoreView.as_view(), name='unitoperation_restore'),
    path('unit-operations/<uuid:pk>/reorder/<str:direction>/', views.UnitOperationReorderView.as_view(),
         name='unitoperation_reorder'),
    path('unit-operations/<uuid:pk>/detail/', views.UnitOperationDetailView.as_view(), name='unitoperation_detail'),

    # =========================================================================
    # LEVEL 3 : STEPS
    # =========================================================================
    path('unit-operations/<uuid:unit_pk>/manage/', views.StepStructureView.as_view(), name='step_list'),
    path('unit-operations/<uuid:unit_pk>/manage/add/', views.StepAddView.as_view(), name='step_add'),
    path('steps/<uuid:pk>/edit/', views.StepUpdateView.as_view(), name='step_edit'),
    path('steps/<uuid:pk>/delete/', views.StepDeleteView.as_view(), name='step_delete'),
    path('steps/<uuid:pk>/restore/', views.StepRestoreView.as_view(), name='step_restore'),
    path('steps/<uuid:pk>/reorder/<str:direction>/', views.StepReorderView.as_view(), name='step_reorder'),
    path('steps/<uuid:pk>/detail/', views.StepDetailView.as_view(), name='step_detail'),

    # =========================================================================
    # LEVEL 4.1 : PARAMETERS
    # =========================================================================
    path('steps/<uuid:step_pk>/parameters/', views.ParameterStructureView.as_view(), name='parameter_list'),
    path('steps/<uuid:step_pk>/parameters/add/', views.ParameterAddView.as_view(), name='parameter_add'),
    path('parameters/<uuid:pk>/edit/', views.ParameterUpdateView.as_view(), name='parameter_edit'),
    path('parameters/<uuid:pk>/delete/', views.ParameterDeleteView.as_view(), name='parameter_delete'),
    path('parameters/<uuid:pk>/restore/', views.ParameterRestoreView.as_view(), name='parameter_restore'),
    path('parameters/<uuid:pk>/reorder/<str:direction>/', views.ParameterReorderView.as_view(),
         name='parameter_reorder'),
    path('parameters/<uuid:pk>/detail/', views.ParameterDetailView.as_view(), name='parameter_detail'),

    # =========================================================================
    # LEVEL 4.2 : SAMPLING PLANS
    # =========================================================================
    path('steps/<uuid:step_pk>/samplingplans/', views.SamplingPlanStructureView.as_view(), name='samplingplan_list'),
    path('steps/<uuid:step_pk>/samplingplans/add/', views.SamplingPlanAddView.as_view(), name='samplingplan_add'),
    path('samplingplans/<uuid:pk>/edit/', views.SamplingPlanUpdateView.as_view(), name='samplingplan_edit'),
    path('samplingplans/<uuid:pk>/delete/', views.SamplingPlanDeleteView.as_view(), name='samplingplan_delete'),
    path('samplingplans/<uuid:pk>/restore/', views.SamplingPlanRestoreView.as_view(), name='samplingplan_restore'),
    path('samplingplans/<uuid:pk>/detail/', views.SamplingPlanDetailView.as_view(), name='samplingplan_detail'),

    # =========================================================================
    # LEVEL 4.3 : SAMPLES
    # =========================================================================
    path('samplingplans/<uuid:sampling_plan_pk>/samples/', views.SampleStructureView.as_view(), name='sample_list'),
    path('samplingplans/<uuid:sampling_plan_pk>/samples/add/', views.SampleAddView.as_view(), name='sample_add'),
    path('samples/<uuid:pk>/edit/', views.SampleUpdateView.as_view(), name='sample_edit'),
    path('samples/<uuid:pk>/delete/', views.SampleDeleteView.as_view(), name='sample_delete'),
    path('samples/<uuid:pk>/restore/', views.SampleRestoreView.as_view(), name='sample_restore'),
    path('samples/<uuid:pk>/detail/', views.SampleDetailView.as_view(), name='sample_detail'),
]
