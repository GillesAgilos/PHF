from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Process, UnitOperation, Sequence, Parameter, Step


class MethodologyLogicTest(TestCase):
    """
    Test suite for the Methodology app, covering:
    1. Hierarchical integrity (Process -> UnitOp -> Sequence)
    2. Audit Trail (via AuditTrailMixin)
    3. Soft Delete and protection of manufacturing recipes
    4. Form filtering (only active parameters/ops allowed)
    """

    def setUp(self):
        # 1. User for Audit Trail
        self.user = User.objects.create_user(
            username='lab_tech',
            password='password123'
        )

        # 2. Base Methodology Data
        self.process = Process.objects.create(
            name="Monoclonal Antibody Alpha",
            scale="2000L",
            created_by=self.user
        )

        self.unit_op = UnitOperation.objects.create(
            name="Protein A Chromatography",
            category="DSP",
            created_by=self.user
        )

        self.parameter = Parameter.objects.create(
            name="Flow Rate",
            unit="cm/h",
            range_values="150-300",
            created_by=self.user
        )

    # ==========================================
    # HIERARCHY & INTEGRITY TESTS
    # ==========================================

    def test_sequence_creation_audit(self):
        """Verify Sequence correctly links to UnitOp and tracks creator"""
        sequence = Sequence.objects.create(
            unit_operation=self.unit_op,
            name="Column Loading",
            order=1,
            created_by=self.user
        )
        self.assertEqual(sequence.unit_operation.name, "Protein A Chromatography")
        self.assertEqual(sequence.created_by, self.user)

    def test_step_parameter_linking(self):
        """Verify a Step correctly binds a Parameter to a Sequence"""
        seq = Sequence.objects.create(unit_operation=self.unit_op, name="Elution", order=2)
        step = Step.objects.create(
            sequence=seq,
            parameter=self.parameter,
            instructed_value="250"
        )
        self.assertEqual(step.parameter.unit, "cm/h")
        self.assertEqual(step.instructed_value, "250")

    # ==========================================
    # VIEW & AUDIT TRAIL TESTS (Mixin Test)
    # ==========================================

    def test_process_create_view_audit(self):
        """Test if AuditTrailMixin correctly assigns users in the UI"""
        self.client.login(username='lab_tech', password='password123')

        post_data = {'name': 'New Bio Process', 'scale': '500L'}
        response = self.client.post(reverse('methodology:process_add'), data=post_data)

        self.assertEqual(response.status_code, 302)
        new_process = Process.objects.get(name='New Bio Process')
        self.assertEqual(new_process.created_by, self.user)
        self.assertEqual(new_process.updated_by, self.user)

    # ==========================================
    # ARCHIVE PROTECTION TESTS
    # ==========================================

    def test_cannot_modify_archived_unit_op(self):
        """Business Rule: Archived Unit Operations must be locked"""
        self.unit_op.is_active = False
        self.unit_op.save()

        self.unit_op.name = "Illegal Update"
        with self.assertRaises(PermissionError):
            self.unit_op.save()

    def test_restore_process(self):
        """Check if an archived process can be restored through the generic view"""
        self.process.is_active = False
        self.process.save()

        self.client.login(username='lab_tech', password='password123')
        url = reverse('methodology:restore', kwargs={'model_nm': 'process', 'pk': self.process.pk})

        self.client.post(url)
        self.process.refresh_from_db()
        self.assertTrue(self.process.is_active)

    # ==========================================
    # FORM FILTERING TESTS
    # ==========================================

    def test_form_excludes_inactive_unit_ops(self):
        """Ensure archived UnitOps don't appear when building a Process Structure"""
        # Create an archived Unit Op
        archived_op = UnitOperation.objects.create(name="Old Op", category="USP", is_active=False)

        self.client.login(username='lab_tech', password='password123')
        # We assume you have a view for adding structure or check the form directly
        from .forms import ProcessStructureForm
        form = ProcessStructureForm()

        self.assertNotIn(archived_op, form.fields['unit_operation'].queryset)
        self.assertIn(self.unit_op, form.fields['unit_operation'].queryset)

# ==============================================================================
# SUMMARY OF TEST COVERAGE - METHODOLOGY APP
# ==============================================================================
# 1. RECIPE INTEGRITY: Checks the correct nesting of Processes, Ops, and Steps.
# 2. AUTOMATED AUDIT: Validates that AuditTrailMixin correctly captures the
#    logged-in user without manual assignment in every view.
# 3. GxP COMPLIANCE: Ensures archived methodology (old recipes) cannot be
#    altered, preventing historical data corruption.
# 4. SAFETY FILTERING: Confirms that technicians can only select 'Active'
#    parameters and operations when designing new processes.
#
# Command to run: python manage.py test methodology
# ==============================================================================