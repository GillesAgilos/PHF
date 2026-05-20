# referential/tests.py
from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from .models import Client, MoleculeType, Project, AnalyticalMethod
from .forms import ClientForm, MoleculeTypeForm, ProjectForm, AnalyticalMethodForm
from phf.utils_tests import BaseEntityTestMixin  # Ajuste le chemin d'import si nécessaire


# ==========================================
# MOLECULE TYPE TESTS
# ==========================================
class TestMoleculeType(BaseEntityTestMixin, TestCase):
    model = MoleculeType
    form_class = MoleculeTypeForm
    app_namespace = 'referential'

    def get_valid_factory_data(self) -> dict:
        return {
            'name': 'Small Molecule',
            'description': 'Standard small molecule therapeutic description.'
        }

    def test_filter_state_behavior(self):
        self.create_instance(name="Draft Molecule", status="DRAFT", is_active=True)
        self.create_instance(name="Validated Molecule", status="VALIDATED", is_active=True)
        self.create_instance(name="Archived Molecule", is_active=False)

        url = reverse(f"{self.app_namespace}:moleculetype_list")

        # Vue "To Validate" -> Attend le brouillon (DRAFT)
        response = self.client.get(f"{url}?view=pending")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Draft Molecule", str(response.content))

        # Vue active -> Attend l'élément validé (VALIDATED)
        response = self.client.get(f"{url}?view=active")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Validated Molecule", str(response.content))


# ==========================================
# CLIENT TESTS
# ==========================================
class TestClient(BaseEntityTestMixin, TestCase):
    model = Client
    form_class = ClientForm
    app_namespace = 'referential'

    def get_valid_factory_data(self) -> dict:
        return {
            'name': 'ACME Pharmaceuticals',
            'code': 'ACME-001'
        }

    def test_filter_state_behavior(self):
        self.create_instance(name="Client Draft", code="CL-D", status="DRAFT", is_active=True)
        self.create_instance(name="Client Validated", code="CL-V", status="VALIDATED", is_active=True)

        url = reverse(f"{self.app_namespace}:client_list")

        # Vue "To Validate" -> Attend le brouillon
        response = self.client.get(f"{url}?view=pending")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Client Draft", str(response.content))


# ==========================================
# PROJECT TESTS
# ==========================================
class TestProject(BaseEntityTestMixin, TestCase):
    model = Project
    form_class = ProjectForm
    app_namespace = 'referential'

    def get_valid_factory_data(self) -> dict:
        # On s'assure d'avoir des relations valides pour passer le full_clean()
        self.client_fk = Client.objects.create(name='Valid Client', code='VAL-CLI', status='VALIDATED', is_active=True)
        self.molecule_fk = MoleculeType.objects.create(name='Valid Molecule', status='VALIDATED', is_active=True)

        return {
            'name': 'Project Prototype',
            'code': 'PRJ-PROTO',
            'molecule_name': 'Proto-X',
            'client': self.client_fk,
            'molecule_type': self.molecule_fk
        }

    def test_clean_raises_error_on_unvalidated_relations(self):
        valid_data = self.get_valid_factory_data()
        invalid_client = Client.objects.create(name='Draft Client', code='DRF-CLI', status='DRAFT', is_active=True)

        project = Project(
            name='Project Fail', code='PRJ-FAIL', molecule_name='Fail-1',
            client=invalid_client,
            molecule_type=valid_data['molecule_type']
        )

        with self.assertRaises(ValidationError):
            project.full_clean()

    def test_filter_state_behavior(self):
        data = self.get_valid_factory_data()
        self.model.objects.create(**data)  # Crée l'instance en DRAFT par défaut

        url = reverse(f"{self.app_namespace}:project_list")

        # Vue "To Validate" -> Attend le brouillon
        response = self.client.get(f"{url}?view=pending")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Project Prototype", str(response.content))


# ==========================================
# ANALYTICAL METHOD TESTS
# ==========================================
class TestAnalyticalMethod(BaseEntityTestMixin, TestCase):
    model = AnalyticalMethod
    form_class = AnalyticalMethodForm
    app_namespace = 'referential'

    def get_valid_factory_data(self) -> dict:
        return {
            'name': 'HPLC Quant',
            'volume_required': 2.5,
            'storage_temp': '2-8°C'
        }

    def test_filter_state_behavior(self):
        self.create_instance(name="Method Draft", status="DRAFT")

        url = reverse(f"{self.app_namespace}:analyticalmethod_list")

        # Vue "To Validate" -> Attend le brouillon
        response = self.client.get(f"{url}?view=pending")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Method Draft", str(response.content))