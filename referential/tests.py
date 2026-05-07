from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Client, Project, MoleculeType


class ReferentialLogicTest(TestCase):
    """
    Test suite for the Referential app updated for MoleculeType and GxP compliance.
    """

    def setUp(self):
        # 1. User for Audit Trail
        self.user = User.objects.create_user(
            username='testworker',
            password='password123',
            is_active=True
        )

        # 2. Molecule Type (Required for Projects)
        self.mol_type = MoleculeType.objects.create(
            name="Monoclonal Antibody",
            description="mAbs for testing",
            created_by=self.user
        )

        # 3. Client
        self.client_obj = Client.objects.create(
            name="Eurogentec Test",
            code="EGT-01",
            is_active=True,
            created_by=self.user
        )

    # ==========================================
    # MODEL LOGIC TESTS
    # ==========================================

    def test_soft_delete_and_restore(self):
        """Verifies the delete/restore cycle on MoleculeType"""
        mol = MoleculeType.objects.create(name="To Archive", created_by=self.user)

        # Delete
        mol.delete(user=self.user)
        mol.refresh_from_db()
        self.assertFalse(mol.is_active)
        self.assertEqual(mol.deleted_by, self.user)

        # Restore
        mol.restore()
        mol.refresh_from_db()
        self.assertTrue(mol.is_active)
        self.assertIsNone(mol.deleted_by)

    def test_modification_forbidden_on_archived_object(self):
        """Business Rule: Prevent saving changes on archived objects (BaseModel logic)"""
        self.client_obj.is_active = False
        self.client_obj.save()  # Le premier save pour archiver est permis

        self.client_obj.name = "Forbidden Change"
        with self.assertRaises(PermissionError):
            self.client_obj.save()

    # ==========================================
    # MOLECULE TYPE TESTS
    # ==========================================

    def test_moleculetype_audit_trail_on_create(self):
        """Checks if created_by is assigned via View"""
        self.client.login(username='testworker', password='password123')

        post_data = {'name': 'Vaccine', 'description': 'mRNA platform'}
        response = self.client.post(reverse('referential:molecule_type_add'), data=post_data)

        self.assertEqual(response.status_code, 302)
        new_type = MoleculeType.objects.get(name='Vaccine')
        self.assertEqual(new_type.created_by, self.user)

    # ==========================================
    # PROJECT SPECIFIC TESTS
    # ==========================================

    def test_project_creation_with_relations(self):
        """Verify project creation with Client and MoleculeType ForeignKeys"""
        self.client.login(username='testworker', password='password123')

        post_data = {
            'client': self.client_obj.unique_id,
            'molecule_type': self.mol_type.unique_id,
            'name': 'BioPharma Project',
            'code': 'BPH-99',
            'molecule_name': 'EGT-mAb-01'
        }

        response = self.client.post(reverse('referential:project_add'), data=post_data)
        self.assertEqual(response.status_code, 302)

        new_project = Project.objects.get(code='BPH-99')
        self.assertEqual(new_project.molecule_type, self.mol_type)
        self.assertEqual(new_project.created_by, self.user)

    def test_project_form_filtering(self):
        """Ensure archived MoleculeTypes do not appear in the Project creation form"""
        archived_mol = MoleculeType.objects.create(name="Old Tech", is_active=False)

        self.client.login(username='testworker', password='password123')
        url = reverse('referential:project_add')
        response = self.client.get(url)

        # Check if archived_mol is in the dropdown queryset
        queryset = response.context['form'].fields['molecule_type'].queryset
        self.assertNotIn(archived_mol, queryset)

    def test_cannot_update_archived_project(self):
        """Verify UI level protection (messages.error) in UpdateView"""
        project = Project.objects.create(
            client=self.client_obj,
            molecule_type=self.mol_type,
            name="Archived Proj",
            code="ARC-01",
            molecule_name="Test",
            is_active=False
        )

        self.client.login(username='testworker', password='password123')
        url = reverse('referential:project_edit', kwargs={'pk': project.unique_id})

        response = self.client.post(url, data={
            'name': 'Illegal Change',
            'code': 'ARC-01',
            'client': self.client_obj.unique_id,
            'molecule_type': self.mol_type.unique_id,
            'molecule_name': 'Test'
        }, follow=True)

        # Check for error message and redirection
        self.assertContains(response, "Error: project is archived")
        project.refresh_from_db()
        self.assertNotEqual(project.name, 'Illegal Change')

    # ==========================================
    # SECURITY
    # ==========================================

    def test_unauthenticated_access(self):
        """Verify unauthenticated users cannot see data"""
        url = reverse('referential:client_list')
        response = self.client.get(url)
        # 302 is redirect to login (if login_required middleware/decorator is active)
        self.assertIn(response.status_code, [302, 403])