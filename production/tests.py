from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import ProtectedError

# Imports des modèles des 3 apps
from referential.models import Client, Project, AnalyticalMethod
from methodology.models import Process, UnitOperation, Sequence, Parameter, Step
from .models import Batch, SamplingPlan, Sample, SampleResult


class ProductionLogicTest(TestCase):
    """
    Test suite for the Production app, covering:
    1. Cross-app relations (Batch -> Project & Process)
    2. GxP Data Integrity (Locked archived batches)
    3. Production Execution (Sample collection linked to Steps)
    4. Form safety (Filtering inactive referential data)
    5. Database constraints (PROTECT logic)
    """

    def setUp(self):
        # 1. Setup User (Required for Audit Trail)
        self.user = User.objects.create_user(
            username='prod_manager',
            password='password123'
        )

        # 2. Setup Referential dependencies
        self.client_obj = Client.objects.create(
            name="EGT Bio",
            code="EGTB",
            created_by=self.user
        )
        self.project = Project.objects.create(
            client=self.client_obj,
            name="Project X",
            code="PX-01",
            created_by=self.user
        )
        self.method = AnalyticalMethod.objects.create(
            name="pH Test",
            volume="10ml",
            storage_temp="RT",
            created_by=self.user
        )

        # 3. Setup Methodology dependencies
        self.process = Process.objects.create(
            name="Standard mAb",
            scale="500L",
            created_by=self.user
        )
        self.unit_op = UnitOperation.objects.create(
            name="Filtration",
            category="USP",
            created_by=self.user
        )
        self.seq = Sequence.objects.create(
            unit_operation=self.unit_op,
            name="Filter Run",
            order=1,
            created_by=self.user
        )
        self.param = Parameter.objects.create(
            name="Pressure",
            unit="bar",
            range_values="1-2",
            created_by=self.user
        )
        self.step = Step.objects.create(
            sequence=self.seq,
            parameter=self.param,
            instructed_value="1.5",
            created_by=self.user
        )

        # 4. Setup initial Batch for production tests
        self.batch = Batch.objects.create(
            project=self.project,
            process=self.process,
            iteration_number=101,
            category="M-",
            start_date=timezone.now(),
            created_by=self.user
        )

    # ==========================================
    # CORE LOGIC TESTS
    # ==========================================

    def test_batch_str_representation(self):
        """Verify the naming convention M-101 (ProjectCode)"""
        self.assertEqual(str(self.batch), "M-101 (PX-01)")

    def test_sample_linked_to_step(self):
        """Verify a sample correctly tracks which methodology step it belongs to"""
        sample = Sample.objects.create(
            step=self.step,
            phase="In-Process",
            sample_date=timezone.now(),
            created_by=self.user
        )
        self.assertEqual(sample.step.instructed_value, "1.5")
        self.assertEqual(sample.step.parameter.name, "Pressure")

    # ==========================================
    # GxP PROTECTION TESTS
    # ==========================================

    def test_cannot_modify_archived_batch(self):
        """Business Rule: Once a batch is archived, it must be immutable"""
        self.batch.is_active = False
        self.batch.save()  # Saves the archive status

        self.batch.iteration_number = 999
        # BaseModel save() should raise PermissionError on archived objects
        with self.assertRaises(PermissionError):
            self.batch.save()

    def test_protect_referenced_process(self):
        """
        Verify that a Process cannot be physically deleted if a Batch uses it.
        Bypasses soft-delete to trigger SQL-level PROTECT.
        """
        with self.assertRaises(ProtectedError):
            # Using queryset delete() bypasses the custom BaseModel.delete()
            Process.objects.filter(unique_id=self.process.unique_id).delete()

    # ==========================================
    # VIEW & FORM TESTS
    # ==========================================

    def test_batch_create_view_filters_active(self):
        """Ensure the Batch form only allows selecting active Projects"""
        # Archive the project used in setUp
        self.project.is_active = False
        self.project.save()

        self.client.login(username='prod_manager', password='password123')
        url = reverse('production:batch_add')
        response = self.client.get(url)

        # Check the queryset of the 'project' field in the form
        form_projects = response.context['form'].fields['project'].queryset
        self.assertNotIn(self.project, form_projects)

    def test_result_entry_audit_trail(self):
        """Verify that entering a result automatically tags the user via Mixin"""
        plan = SamplingPlan.objects.create(
            batch=self.batch,
            analytical_method=self.method,
            sample_name="S1",
            created_by=self.user
        )

        self.client.login(username='prod_manager', password='password123')

        post_data = {
            'sampling_plan': plan.unique_id,
            'value': '7.2',
            'unit': 'pH'
        }

        url = reverse('production:result_add')
        response = self.client.post(url, data=post_data)

        self.assertEqual(response.status_code, 302)  # Redirect after success

        new_result = SampleResult.objects.get(value='7.2')
        self.assertEqual(new_result.created_by, self.user)
        self.assertEqual(new_result.sampling_plan.batch, self.batch)

# ==============================================================================
# SUMMARY OF TEST COVERAGE - PRODUCTION APP
# ==============================================================================
# 1. BATCH INTEGRITY: Links high-level Project/Process to execution.
# 2. TRACEABILITY: Ensures physical samples are tied to methodology steps.
# 3. GxP COMPLIANCE: Validates data immutability for archived records.
# 4. REFERENTIAL SAFETY: Tests the 'on_delete=PROTECT' at the database level.
# 5. AUDIT TRAIL: Verifies automated user tracking on analysis entries.
#
# Command: python manage.py test production
# ==============================================================================