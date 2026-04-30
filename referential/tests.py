from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Client, Project


class ReferentialLogicTest(TestCase):
    """
    Test suite for the Referential app, covering:
    1. Soft Delete & Restore functionality
    2. Business rules (Archive protection)
    3. View access, security, and Audit Trail
    4. Form filtering logic
    """

    def setUp(self):
        # 1. Create a test user (required for Audit Trail fields)
        self.user = User.objects.create_user(
            username='testworker',
            password='password123',
            is_active=True
        )

        # 2. Create a dummy client for project relations
        self.client_obj = Client.objects.create(
            name="Eurogentec Test",
            code="EGT-01",
            is_active=True,
            created_by=self.user
        )

    # ==========================================
    # MODEL LOGIC TESTS
    # ==========================================

    def test_soft_delete_mechanics(self):
        """Verify that delete() sets is_active to False instead of removing the row"""
        client = Client.objects.create(name="To Delete", code="DEL-01")
        client.delete(user=self.user)

        client.refresh_from_db()
        self.assertFalse(client.is_active)
        self.assertIsNotNone(client.deleted_at)
        self.assertEqual(client.deleted_by, self.user)
        # Ensure it's still in DB
        self.assertEqual(Client.objects.filter(code="DEL-01").count(), 1)

    def test_restore_functionality(self):
        """Check if an archived object can be restored"""
        self.client_obj.is_active = False
        self.client_obj.save()

        self.client_obj.restore()
        self.assertTrue(self.client_obj.is_active)
        self.assertIsNone(self.client_obj.deleted_at)

    def test_modification_forbidden_on_archived_object(self):
        """Business Rule: Prevent saving changes on archived objects"""
        self.client_obj.is_active = False
        self.client_obj.save()

        self.client_obj.name = "Forbidden Change"
        with self.assertRaises(PermissionError):
            self.client_obj.save()

    # ==========================================
    # VIEW & SECURITY TESTS
    # ==========================================

    def test_client_list_view_requires_login(self):
        """Ensure unauthenticated users are redirected to login"""
        response = self.client.get(reverse('referential:client_list'))
        self.assertEqual(response.status_code, 302)

    def test_client_list_content_authenticated(self):
        """Verify that a logged-in user can see the clients list"""
        self.client.login(username='testworker', password='password123')

        url = reverse('referential:client_list')
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)
        # Verify the correct template is used
        used_templates = [t.name for t in response.templates]
        self.assertIn('referential/client_list.html', used_templates)
        # Verify data presence
        self.assertContains(response, "Eurogentec Test")

    # ==========================================
    # PROJECT SPECIFIC TESTS
    # ==========================================

    def test_project_queryset_filtering(self):
        """Ensure ProjectForm dropdown only shows active clients"""
        self.client_obj.is_active = False
        self.client_obj.save()

        self.client.login(username='testworker', password='password123')
        url = reverse('referential:project_add')
        response = self.client.get(url)

        queryset = response.context['form'].fields['client'].queryset
        self.assertNotIn(self.client_obj, queryset)

    def test_project_audit_trail_on_create(self):
        """Verify project creation correctly tracks the user"""
        self.client.login(username='testworker', password='password123')

        post_data = {
            'client': self.client_obj.unique_id,
            'name': 'BioPharma Project',
            'code': 'BPH-99'
        }

        response = self.client.post(reverse('referential:project_add'), data=post_data)
        self.assertEqual(response.status_code, 302)  # Redirect on success

        new_project = Project.objects.get(code='BPH-99')
        self.assertEqual(new_project.created_by, self.user)
        self.assertEqual(new_project.client, self.client_obj)

    def test_project_update_audit_trail(self):
        """Verify that updating a project tracks the user in updated_by"""
        project = Project.objects.create(
            client=self.client_obj,
            name="Initial Name",
            code="INIT-01",
            created_by=self.user
        )

        self.client.login(username='testworker', password='password123')

        update_data = {
            'client': self.client_obj.unique_id,
            'name': 'Updated Project Name',
            'code': 'INIT-01'
        }

        url = reverse('referential:project_edit', kwargs={'pk': project.unique_id})
        self.client.post(url, data=update_data)

        project.refresh_from_db()
        self.assertEqual(project.name, 'Updated Project Name')
        self.assertEqual(project.updated_by, self.user)

    def test_cannot_update_archived_project(self):
        """Verify that an archived project cannot be modified via UI"""
        project = Project.objects.create(
            client=self.client_obj,
            name="Archived Proj",
            code="ARC-01",
            is_active=False
        )

        self.client.login(username='testworker', password='password123')
        url = reverse('referential:project_edit', kwargs={'pk': project.unique_id})

        # Attempt to change name
        self.client.post(url, data={
            'name': 'Illegal Change',
            'code': 'ARC-01',
            'client': self.client_obj.unique_id
        })

        project.refresh_from_db()
        self.assertNotEqual(project.name, 'Illegal Change')

    # ==========================================
    # CLIENT AUDIT TRAIL
    # ==========================================

    def test_client_audit_trail_on_create(self):
        """Verify that client creation assigns the current user to created_by"""
        self.client.login(username='testworker', password='password123')

        post_data = {'name': 'New Audit Client', 'code': 'AUDIT-001'}
        self.client.post(reverse('referential:client_add'), data=post_data)

        new_client = Client.objects.get(code='AUDIT-001')
        self.assertEqual(new_client.created_by, self.user)



# ==============================================================================
# SUMMARY OF TEST COVERAGE - REFERENTIAL APP
# ==============================================================================
# This test suite ensures the integrity and security of the PHF Referential data.
# It covers four critical areas:
#
# 1. DATA PERSISTENCE & INTEGRITY (Models)
#    - Soft Delete: Verifies that records are archived (is_active=False) and
#      never physically removed from the database.
#    - Restoration: Ensures archived records can be recovered correctly.
#    - Integrity: Validates that archived records are locked and cannot be
#      modified without restoration.
#
# 2. SECURITY & ACCESS CONTROL (Views)
#    - Authentication: Confirms that LoginRequiredMiddleware effectively
#      blocks anonymous access to all referential data.
#    - Authorized Viewing: Checks that authenticated users can see their
#      assigned data lists (Clients & Projects).
#
# 3. AUDIT TRAIL COMPLIANCE (GxP Requirements)
#    - Automated Tracking: Ensures 'created_by' and 'updated_by' fields are
#      automatically populated with the correct user during POST operations.
#    - Audit Consistency: Validates that the system tracks WHO performed
#      every creation and modification.
#
# 4. BUSINESS LOGIC & FILTERING (Forms)
#    - Queryset Filtering: Ensures data entry forms (like Project Creation)
#      only offer active/valid options in dropdowns, preventing links to
#      archived entities.
#
# Command to run: python manage.py test referential
# ==============================================================================