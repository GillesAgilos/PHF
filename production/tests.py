from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import IntegrityError
from .models import Process, UnitOperation, Step, Parameter


class ProductionLogicTest(TestCase):
    """
    Test suite for the Production app ensuring GxP compliance:
    Audit Trail, Soft Delete, and Structural Integrity.
    """

    def setUp(self):
        # 1. Setup User for Audit Trail
        self.user = User.objects.create_user(
            username='qa_specialist',
            password='password123'
        )
        self.client.login(username='qa_specialist', password='password123')

        # 2. Setup Base Hierarchy
        # Note: using .pk instead of .id as your models use UUIDs
        self.process = Process.objects.create(
            code="PR-01",
            scale="10L",
            created_by=self.user
        )
        self.unit = UnitOperation.objects.create(
            process=self.process,
            name="Centrifugation",
            unit_type="USP",
            order=1,
            created_by=self.user
        )

    # ==========================================
    # SOFT DELETE & ARCHIVING TESTS
    # ==========================================

    def test_soft_delete_logic(self):
        """Verify that delete() archives the object instead of physical removal."""
        unit_pk = self.unit.pk
        self.unit.delete(user=self.user)

        # Object must still exist in database but marked as inactive
        unit_from_db = UnitOperation.objects.get(pk=unit_pk)
        self.assertFalse(unit_from_db.is_active)
        self.assertEqual(unit_from_db.deleted_by, self.user)

    def test_modification_forbidden_on_archived_object(self):
        """GxP Requirement: Prevent saving changes on archived records."""
        self.process.is_active = False
        self.process.save()  # Initial save to archive is allowed

        self.process.scale = "500L"
        # BaseModel.save() should raise PermissionError if is_active is False
        with self.assertRaises(PermissionError):
            self.process.save()

    # ==========================================
    # STRUCTURAL INTEGRITY & REORDERING
    # ==========================================

    def test_unique_order_constraint(self):
        """Database Rule: Prevent duplicate 'order' within the same parent."""
        with self.assertRaises(IntegrityError):
            UnitOperation.objects.create(
                process=self.process,
                name="Duplicate Order Unit",
                unit_type="DSP",
                order=1  # Already taken by self.unit
            )

    def test_reorder_view_logic(self):
        """Verify the swap logic between two units in the same process."""
        unit2 = UnitOperation.objects.create(
            process=self.process, name="Filtration", unit_type="DSP", order=2
        )

        # Trigger 'up' movement for the second unit
        url = reverse('production:unit_reorder', kwargs={'pk': unit2.pk, 'direction': 'up'})
        self.client.get(url)

        unit2.refresh_from_db()
        self.unit.refresh_from_db()

        self.assertEqual(unit2.order, 1)
        self.assertEqual(self.unit.order, 2)

    # ==========================================
    # GxP PARAMETERS (PAR/NOR)
    # ==========================================

    def test_parameter_ranges_logic(self):
        """Ensure PAR and NOR ranges are correctly stored."""
        step = Step.objects.create(unit_operation=self.unit, name="S1", order=1)

        param = Parameter.objects.create(
            step=step,
            name="Temperature",
            order=1,
            low_proven_acceptable_range=20.0,
            high_proven_acceptable_range=40.0,
            low_normal_operating_range=36.0,
            high_normal_operating_range=38.0
        )

        self.assertEqual(param.low_normal_operating_range, 36.0)
        # Business logic check: NOR should be inside PAR
        self.assertTrue(param.low_proven_acceptable_range <= param.low_normal_operating_range)
        self.assertTrue(param.high_proven_acceptable_range >= param.high_normal_operating_range)

    # ==========================================
    # UI & VIEW PROTECTION
    # ==========================================

    def test_ui_protection_on_archived_process(self):
        """Check that AuditTrailMixin blocks updates via UI for archived objects."""
        self.process.is_active = False
        self.process.save()

        url = reverse('production:process_edit', kwargs={'pk': self.process.pk})
        response = self.client.post(url, {'code': 'HACK', 'scale': '999L'}, follow=True)

        # Should display error message and redirect
        self.assertContains(response, f"Error: This Process is archived.")
        self.process.refresh_from_db()
        self.assertEqual(self.process.code, "PR-01")  # Value remained unchanged

    def test_form_validation_duplicate_order(self):
        """Verify that the StepForm clean_order method prevents duplicates."""
        Step.objects.create(unit_operation=self.unit, name="Step 1", order=1)

        url = reverse('production:step_add', kwargs={'unit_pk': self.unit.pk})
        response = self.client.post(url, {'name': 'Step 2', 'order': 1})  # Conflict

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'order', "Step order 1 already exists for this unit.")

    # ==========================================
    # SECURITY
    # ==========================================

    def test_anonymous_access_denied(self):
        """Anonymous users must be redirected to login."""
        self.client.logout()
        url = reverse('production:process_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)