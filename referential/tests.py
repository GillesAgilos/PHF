from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from production.models import Process
from .forms import (
    AnalyticalMethodForm,
    ClientForm,
    GlobalUnitOperationForm,
    MoleculeTypeForm,
    ProjectForm,
)
from .models import AnalyticalMethod, Client, GlobalUnitOperation, MoleculeType, Project
from .views import get_catalog_process


class ReferentialTestDataMixin:
    """
    Mixin providing test data setup for models and related group/user configurations.

    This class is designed to create and configure representative test data for various
    application models, including users, groups, clients, molecule types, projects,
    analytical methods, and global unit operations. It establishes default validation
    states, relationships, and instance lifecycles (e.g., archived or deleted states)
    to ensure consistency and coverage in test environments.

    Attributes:
        system_admin_group (Group): Group assigned for system administrators.
        data_steward_group (Group): Group assigned for data stewards.
        qa_group (Group): Group assigned for QA representatives.
        admin (User): A system administrator user with superuser and staff privileges.
        steward (User): A data steward user associated with the data steward group.
        qa (User): A QA representative user associated with the QA group.
        validated_client (Client): A validated client instance with the status set
            to VALIDATED.
        draft_client (Client): A client instance with the status set to draft
            (default state).
        archived_client (Client): A client instance with the status previously set to
            VALIDATED but has since been archived (deleted).
        rejected_client (Client): A client instance with the status set to REJECTED.
        validated_molecule_type (MoleculeType): A molecule type instance marked as
            VALIDATED.
        draft_molecule_type (MoleculeType): A molecule type instance with the status set
            to draft (default state).
        archived_molecule_type (MoleculeType): A molecule type instance previously marked
            as VALIDATED but has since been archived (deleted).
        validated_project (Project): A project instance with the status set to VALIDATED.
        validated_method (AnalyticalMethod): An analytical method instance marked as
            VALIDATED.
        validated_global_unit (GlobalUnitOperation): A global unit operation instance
            marked as VALIDATED.
    """
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        cls.system_admin_group = Group.objects.create(name="System_Admin")
        cls.data_steward_group = Group.objects.create(name="Data_Steward")
        cls.qa_group = Group.objects.create(name="QA_Representative")

        cls.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass12345",
            is_staff=True,
            is_superuser=True,
        )
        cls.steward = User.objects.create_user(
            username="steward",
            email="steward@example.com",
            password="pass12345",
            is_staff=True,
        )
        cls.steward.groups.add(cls.data_steward_group)

        cls.qa = User.objects.create_user(
            username="qa",
            email="qa@example.com",
            password="pass12345",
            is_staff=True,
        )
        cls.qa.groups.add(cls.qa_group)

        cls.validated_client = Client.objects.create(
            name="Validated Client",
            code="CL-VAL",
            status=Client.Status.VALIDATED,
        )
        cls.draft_client = Client.objects.create(
            name="Draft Client",
            code="CL-DRF",
        )
        cls.archived_client = Client.objects.create(
            name="Archived Client",
            code="CL-ARC",
            status=Client.Status.VALIDATED,
        )
        cls.archived_client.delete(user=cls.admin)
        cls.rejected_client = Client.objects.create(
            name="Rejected Client",
            code="CL-REJ",
            status=Client.Status.REJECTED,
        )

        cls.validated_molecule_type = MoleculeType.objects.create(
            type="Validated Molecule",
            description="Validated molecule type",
            status=MoleculeType.Status.VALIDATED,
        )
        cls.draft_molecule_type = MoleculeType.objects.create(
            type="Draft Molecule",
            description="Draft molecule type",
        )
        cls.archived_molecule_type = MoleculeType.objects.create(
            type="Archived Molecule",
            description="Archived molecule type",
            status=MoleculeType.Status.VALIDATED,
        )
        cls.archived_molecule_type.delete(user=cls.admin)

        cls.validated_project = Project.objects.create(
            code="PRJ-VAL",
            molecule_name="Molecule X",
            client=cls.validated_client,
            molecule_type=cls.validated_molecule_type,
            status=Project.Status.VALIDATED,
        )

        cls.validated_method = AnalyticalMethod.objects.create(
            name="Validated Method",
            unit="mg/L",
            sop_code="SOP-001",
            sop_version="v1",
            status=AnalyticalMethod.Status.VALIDATED,
        )

        cls.validated_global_unit = GlobalUnitOperation.objects.create(
            name="Validated Global Unit",
            unit_type="USP",
            status=GlobalUnitOperation.Status.VALIDATED,
        )


class ReferentialModelTests(ReferentialTestDataMixin, TestCase):
    """
    Tests for verifying the behavior of referential models.

    This class contains tests for validating the string representation, data integrity,
    and uniqueness constraints of referential models, as well as catalog process reuse.
    These tests ensure that referential models behave as expected under various scenarios
    and comply with validation rules defined in the model logic.

    Methods:
        test_string_representations: Validates the string representations of various
            referential models to ensure consistency with expected formats.

        test_project_rejects_unvalidated_or_archived_relations: Ensures that the creation
            of projects with unvalidated or archived related entities raises validation
            errors, preserving data integrity.

        test_project_unique_together_per_client: Verifies that projects are unique within
            a client with regard to specific constraints, preventing duplicates.

        test_get_catalog_process_creates_and_reuses_catalog: Tests that the function for
            retrieving a catalog process reuses an existing draft process, or creates a
            new draft process if none exists.
    """
    def test_string_representations(self):
        self.assertEqual(str(self.validated_client), "CL-VAL - Validated Client")
        self.assertEqual(str(self.validated_molecule_type), "Validated Molecule")
        self.assertEqual(str(self.validated_project), "PRJ-VAL - Validated Client - Molecule X")
        self.assertEqual(str(self.validated_method), "Validated Method")
        self.assertEqual(str(self.validated_global_unit), "Validated Global Unit (USP)")

    def test_project_rejects_unvalidated_or_archived_relations(self):
        with self.assertRaises(ValidationError):
            Project.objects.create(
                code="PRJ-INV-1",
                molecule_name="Molecule Y",
                client=self.draft_client,
                molecule_type=self.validated_molecule_type,
            )

        with self.assertRaises(ValidationError):
            Project.objects.create(
                code="PRJ-INV-2",
                molecule_name="Molecule Y",
                client=self.archived_client,
                molecule_type=self.validated_molecule_type,
            )

    def test_project_unique_together_per_client(self):
        with self.assertRaises(ValidationError):
            Project.objects.create(
                molecule_name="Molecule Y",
                code=self.validated_project.code,
                client=self.validated_client,
                molecule_type=self.validated_molecule_type,
            )

    def test_get_catalog_process_creates_and_reuses_catalog(self):
        process = get_catalog_process()
        self.assertEqual(process.code, "GLOBAL_CATALOG")
        self.assertEqual(process.name, "Global Unit Operation Catalog Repository")
        self.assertEqual(process.status, Process.Status.DRAFT)

        process_again = get_catalog_process()
        self.assertEqual(process.pk, process_again.pk)


class ReferentialFormTests(ReferentialTestDataMixin, TestCase):
    """
    Represents a suite of test cases for validating the behavior and functionality of
    various forms within a referential data context.

    This class inherits from `ReferentialTestDataMixin` and `TestCase` to test the
    validation of forms, the requirement of justification during updates, the exclusion
    of justification during creation, and the restriction of related querysets to those
    entities that are validated and active.

    Attributes:
        validated_client (Client): A validated client instance used in tests.
        draft_client (Client): A draft (non-validated) client instance used in tests.
        archived_client (Client): An archived client instance used in tests.
        validated_molecule_type (MoleculeType): A validated molecule type instance used
            in tests.
        draft_molecule_type (MoleculeType): A draft (non-validated) molecule type
            instance used in tests.
        archived_molecule_type (MoleculeType): An archived molecule type instance used
            in tests.
    """
    def test_base_entity_form_requires_justification_on_update(self):
        form = ClientForm(
            instance=self.validated_client,
            data={
                "name": "Validated Client Updated",
                "code": self.validated_client.code,
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn("change_justification", form.errors)

        form = ClientForm(
            instance=self.validated_client,
            data={
                "name": "Validated Client Updated",
                "code": self.validated_client.code,
                "change_justification": "Business correction",
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        updated = form.save()
        self.assertEqual(updated._change_reason, "Business correction")

    def test_base_entity_form_removes_justification_on_create(self):
        form = ClientForm(data={"name": "New Client", "code": "CL-NEW"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertNotIn("change_justification", form.fields)

    def test_simple_forms_validate(self):
        self.assertTrue(
            MoleculeTypeForm(data={"type": "RNA", "description": "RNA molecules"}).is_valid()
        )
        self.assertTrue(
            AnalyticalMethodForm(
                data={
                    "name": "HPLC",
                    "unit": "mg/L",
                    "sop_code": "SOP-002",
                    "sop_version": "v2",
                }
            ).is_valid()
        )
        self.assertTrue(
            GlobalUnitOperationForm(data={"name": "Purification", "unit_type": "DSP"}).is_valid()
        )

    def test_project_form_limits_related_querysets_to_validated_and_active(self):
        form = ProjectForm()

        client_ids = set(form.fields["client"].queryset.values_list("pk", flat=True))
        molecule_ids = set(form.fields["molecule_type"].queryset.values_list("pk", flat=True))

        self.assertIn(self.validated_client.pk, client_ids)
        self.assertNotIn(self.draft_client.pk, client_ids)
        self.assertNotIn(self.archived_client.pk, client_ids)

        self.assertIn(self.validated_molecule_type.pk, molecule_ids)
        self.assertNotIn(self.draft_molecule_type.pk, molecule_ids)
        self.assertNotIn(self.archived_molecule_type.pk, molecule_ids)


class ReferentialUrlTests(ReferentialTestDataMixin, TestCase):
    """Tests for validating the reverse URL resolution of referential app routes.

    This class contains test cases to ensure all referential app URLs resolve correctly
    and begin with the expected base path "/referential/". It makes use of a series
    of route definitions and performs checks for each route in a systematic manner.

    """
    def test_all_referential_urls_reverse(self):
        route_cases = [
            ("referential:client_list", {}),
            ("referential:client_add", {}),
            ("referential:client_detail", {"pk": self.validated_client.pk}),
            ("referential:client_edit", {"pk": self.validated_client.pk}),
            ("referential:client_delete", {"pk": self.validated_client.pk}),
            ("referential:client_restore", {"pk": self.validated_client.pk}),
            ("referential:client_validate", {"pk": self.validated_client.pk}),
            ("referential:client_reject", {"pk": self.validated_client.pk}),
            ("referential:project_list", {}),
            ("referential:project_add", {}),
            ("referential:project_detail", {"pk": self.validated_project.pk}),
            ("referential:project_edit", {"pk": self.validated_project.pk}),
            ("referential:project_delete", {"pk": self.validated_project.pk}),
            ("referential:project_restore", {"pk": self.validated_project.pk}),
            ("referential:project_validate", {"pk": self.validated_project.pk}),
            ("referential:project_reject", {"pk": self.validated_project.pk}),
            ("referential:moleculetype_list", {}),
            ("referential:moleculetype_add", {}),
            ("referential:moleculetype_detail", {"pk": self.validated_molecule_type.pk}),
            ("referential:moleculetype_edit", {"pk": self.validated_molecule_type.pk}),
            ("referential:moleculetype_delete", {"pk": self.validated_molecule_type.pk}),
            ("referential:moleculetype_restore", {"pk": self.validated_molecule_type.pk}),
            ("referential:moleculetype_validate", {"pk": self.validated_molecule_type.pk}),
            ("referential:moleculetype_reject", {"pk": self.validated_molecule_type.pk}),
            ("referential:analyticalmethod_list", {}),
            ("referential:analyticalmethod_add", {}),
            ("referential:analyticalmethod_detail", {"pk": self.validated_method.pk}),
            ("referential:analyticalmethod_edit", {"pk": self.validated_method.pk}),
            ("referential:analyticalmethod_delete", {"pk": self.validated_method.pk}),
            ("referential:analyticalmethod_restore", {"pk": self.validated_method.pk}),
            ("referential:analyticalmethod_validate", {"pk": self.validated_method.pk}),
            ("referential:analyticalmethod_reject", {"pk": self.validated_method.pk}),
            ("referential:globalunitoperation_list", {}),
            ("referential:globalunitoperation_add", {}),
            ("referential:globalunitoperation_detail", {"pk": self.validated_global_unit.pk}),
            ("referential:globalunitoperation_edit", {"pk": self.validated_global_unit.pk}),
            ("referential:globalunitoperation_delete", {"pk": self.validated_global_unit.pk}),
            ("referential:globalunitoperation_restore", {"pk": self.validated_global_unit.pk}),
            ("referential:globalunitoperation_validate", {"pk": self.validated_global_unit.pk}),
            ("referential:globalunitoperation_reject", {"pk": self.validated_global_unit.pk}),
        ]

        for route_name, kwargs in route_cases:
            with self.subTest(route_name=route_name):
                self.assertTrue(reverse(route_name, kwargs=kwargs).startswith("/referential/"))


class ReferentialSecurityTests(ReferentialTestDataMixin, TestCase):
    """
    Tests the security-related access rules for referential views and actions.

    This class defines and validates permissions for different user roles, ensuring that
    security requirements are adhered to for various referential data operations
    (e.g., adding, editing, deleting, restoring, and validating entities). It
    differentiates access control rules across roles such as anonymous users, data stewards,
    QA members, and system administrators.

    Attributes:
        steward (User): Represents a data steward user with limited privileges.
        qa (User): Represents a quality assurance user with specific referential access.
        admin (User): Represents a system administrator user with full access.
        validated_client (Client): A validated client object used in the tests.
        validated_project (Project): A validated project object used during testing.
        validated_molecule_type (MoleculeType): A validated molecule type instance.
        validated_method (AnalyticalMethod): An analytical method object marked as validated.
        validated_global_unit (GlobalUnitOperation): A validated global unit operation used
            for validation and rejection scenarios.
    """
    def assert_permission_denied(self, method, url_name, user, kwargs=None, data=None):
        self.client.force_login(user)
        kwargs = kwargs or {}
        data = data or {}
        response = getattr(self.client, method)(reverse(url_name, kwargs=kwargs), data)
        self.assertEqual(response.status_code, 403)

    def test_anonymous_users_are_redirected_to_login(self):
        response = self.client.get(reverse("referential:client_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_data_steward_access_rules(self):
        self.client.force_login(self.steward)

        self.assertEqual(self.client.get(reverse("referential:client_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("referential:client_add")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("referential:client_edit", kwargs={"pk": self.validated_client.pk})).status_code,
            200,
        )

        fresh_mt = MoleculeType.objects.create(type="Steward Flow MT", description="x")
        self.assertEqual(
            self.client.post(reverse("referential:moleculetype_delete", kwargs={"pk": fresh_mt.pk})).status_code,
            302,
        )
        fresh_mt.delete(user=self.admin)
        self.assertEqual(
            self.client.post(reverse("referential:moleculetype_restore", kwargs={"pk": fresh_mt.pk})).status_code,
            302,
        )

        self.assert_permission_denied(
            "post",
            "referential:client_delete",
            self.steward,
            kwargs={"pk": self.validated_client.pk},
        )
        self.assert_permission_denied(
            "post",
            "referential:project_restore",
            self.steward,
            kwargs={"pk": self.validated_project.pk},
        )
        self.assert_permission_denied(
            "post",
            "referential:moleculetype_validate",
            self.steward,
            kwargs={"pk": self.validated_molecule_type.pk},
        )
        self.assert_permission_denied(
            "post",
            "referential:moleculetype_reject",
            self.steward,
            kwargs={"pk": self.validated_molecule_type.pk},
            data={"rejection_reason": "No"},
        )

    def test_qa_access_rules(self):
        self.client.force_login(self.qa)

        self.assertEqual(self.client.get(reverse("referential:analyticalmethod_list")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("referential:analyticalmethod_detail", kwargs={"pk": self.validated_method.pk})).status_code,
            200,
        )

        fresh_mt = MoleculeType.objects.create(type="QA Flow MT", description="x")
        self.assertEqual(
            self.client.post(reverse("referential:moleculetype_validate", kwargs={"pk": fresh_mt.pk})).status_code,
            302,
        )
        fresh_mt.refresh_from_db()
        self.assertEqual(fresh_mt.status, MoleculeType.Status.VALIDATED)

        self.assertEqual(
            self.client.post(
                reverse("referential:moleculetype_reject", kwargs={"pk": fresh_mt.pk}),
                data={"rejection_reason": "Incorrect content"},
            ).status_code,
            302,
        )

        self.assert_permission_denied(
            "get",
            "referential:client_add",
            self.qa,
        )
        self.assert_permission_denied(
            "post",
            "referential:client_delete",
            self.qa,
            kwargs={"pk": self.validated_client.pk},
        )
        self.assert_permission_denied(
            "post",
            "referential:project_restore",
            self.qa,
            kwargs={"pk": self.validated_project.pk},
        )

    def test_system_admin_bypass_rules(self):
        self.client.force_login(self.admin)

        self.assertEqual(self.client.get(reverse("referential:project_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("referential:project_add")).status_code, 200)
        self.assertEqual(
            self.client.post(
                reverse("referential:globalunitoperation_validate", kwargs={"pk": self.validated_global_unit.pk})
            ).status_code,
            302,
        )
        self.assertEqual(
            self.client.post(
                reverse("referential:globalunitoperation_reject", kwargs={"pk": self.validated_global_unit.pk}),
                data={"rejection_reason": "Admin test"},
            ).status_code,
            302,
        )


class ReferentialWorkflowTests(ReferentialTestDataMixin, TestCase):
    """
    Unit test suite for testing the full lifecycle of MoleculeType objects.

    This class is responsible for performing end-to-end workflow tests for
    the MoleculeType model. It validates the creation, editing, validation,
    rejection, deletion, and restoration processes of a MoleculeType object.
    The tests ensure that all transitions and updates in the lifecycle conform
    to the expected behaviors and constraints.

    Attributes:
        client (TestClient): Django test client used to perform HTTP requests.
        steward (User): Test user with stewardship privileges to manage objects.
        qa (User): Test user with quality assurance privileges for validation
            and review.
    """
    def test_molecule_type_full_lifecycle(self):
        self.client.force_login(self.steward)

        create_response = self.client.post(
            reverse("referential:moleculetype_add"),
            data={"type": "Lifecycle Molecule", "description": "Lifecycle"},
        )
        self.assertEqual(create_response.status_code, 302)

        molecule = MoleculeType.objects.get(type="Lifecycle Molecule")
        self.assertEqual(molecule.status, MoleculeType.Status.DRAFT)
        self.assertEqual(molecule.created_by, self.steward)
        self.assertEqual(molecule.updated_by, self.steward)
        self.assertTrue(molecule.is_active)

        update_response = self.client.post(
            reverse("referential:moleculetype_edit", kwargs={"pk": molecule.pk}),
            data={
                "type": "Lifecycle Molecule Updated",
                "description": "Lifecycle updated",
                "change_justification": "Corrected naming",
            },
        )
        self.assertEqual(update_response.status_code, 302)
        molecule.refresh_from_db()
        self.assertEqual(molecule.type, "Lifecycle Molecule Updated")
        self.assertEqual(molecule.status, MoleculeType.Status.DRAFT)
        self.assertEqual(molecule.updated_by, self.steward)

        self.client.force_login(self.qa)
        validate_response = self.client.post(
            reverse("referential:moleculetype_validate", kwargs={"pk": molecule.pk})
        )
        self.assertEqual(validate_response.status_code, 302)
        molecule.refresh_from_db()
        self.assertEqual(molecule.status, MoleculeType.Status.VALIDATED)
        self.assertEqual(molecule.updated_by, self.qa)

        reject_response = self.client.post(
            reverse("referential:moleculetype_reject", kwargs={"pk": molecule.pk}),
            data={"rejection_reason": "Needs correction"},
        )
        self.assertEqual(reject_response.status_code, 302)
        molecule.refresh_from_db()
        self.assertEqual(molecule.status, MoleculeType.Status.REJECTED)
        self.assertEqual(molecule.rejection_reason, "Needs correction")
        self.assertEqual(molecule.updated_by, self.qa)

        self.client.force_login(self.steward)
        delete_response = self.client.post(
            reverse("referential:moleculetype_delete", kwargs={"pk": molecule.pk})
        )
        self.assertEqual(delete_response.status_code, 302)
        molecule.refresh_from_db()
        self.assertFalse(molecule.is_active)
        self.assertEqual(molecule.deleted_by, self.steward)

        restore_response = self.client.post(
            reverse("referential:moleculetype_restore", kwargs={"pk": molecule.pk})
        )
        self.assertEqual(restore_response.status_code, 302)
        molecule.refresh_from_db()
        self.assertTrue(molecule.is_active)
        self.assertEqual(molecule.status, MoleculeType.Status.DRAFT)
        self.assertIsNone(molecule.deleted_by)
