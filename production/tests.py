from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from referential.models import AnalyticalMethod, Client, GlobalUnitOperation, MoleculeType, Project
from .forms import AnalysisForm, ParameterForm, ProcessForm, SampleForm, StepForm, UnitOperationForm
from .models import Analysis, Parameter, Process, Sample, Step, UnitOperation


class ProductionTestDataMixin:
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

        cls.client_entity = Client.objects.create(
            name="Validated Client",
            code="CL-001",
            status=Client.Status.VALIDATED,
        )
        cls.molecule_type = MoleculeType.objects.create(
            type="Validated Molecule",
            description="Validated molecule type",
            status=MoleculeType.Status.VALIDATED,
        )
        cls.project = Project.objects.create(
            code="PRJ-001",
            molecule_name="Molecule A",
            client=cls.client_entity,
            molecule_type=cls.molecule_type,
            status=Project.Status.VALIDATED,
        )

        cls.global_unit_usp = GlobalUnitOperation.objects.create(
            name="USP Granulation",
            unit_type="USP",
            status=GlobalUnitOperation.Status.VALIDATED,
        )
        cls.global_unit_dsp = GlobalUnitOperation.objects.create(
            name="DSP Filtration",
            unit_type="DSP",
            status=GlobalUnitOperation.Status.VALIDATED,
        )

        cls.method = AnalyticalMethod.objects.create(
            name="HPLC",
            unit="mg/L",
            sop_code="SOP-001",
            sop_version="v1",
            status=AnalyticalMethod.Status.VALIDATED,
        )
        cls.archived_method = AnalyticalMethod.objects.create(
            name="Archived Method",
            unit="mg/L",
            sop_code="SOP-099",
            sop_version="v9",
            status=AnalyticalMethod.Status.VALIDATED,
        )
        cls.archived_method.delete(user=cls.admin)

        cls.validated_process = Process.objects.create(
            name="Validated Process",
            code="PROC-VAL",
            scale="Pilot",
            version=1,
        )
        cls.validated_unit = UnitOperation.objects.create(
            process=cls.validated_process,
            name=cls.global_unit_usp.name,
            unit_type=cls.global_unit_usp.unit_type,
            order=1,
        )
        cls.validated_step = Step.objects.create(
            unit_operation=cls.validated_unit,
            name="Mixing",
            order=1,
        )
        cls.validated_parameter = Parameter.objects.create(
            step=cls.validated_step,
            name="Temperature",
            unit="C",
            format_type="numeric",
            format_low_range=20.0,
            format_high_range=40.0,
            order=1,
        )
        cls.validated_sample = Sample.objects.create(
            step=cls.validated_step,
            name="Sample A",
        )
        cls.validated_analysis = Analysis.objects.create(
            sample=cls.validated_sample,
            analysis_name="Potency",
            analytical_method=cls.method,
            format_low_range=0.0,
            format_high_range=10.0,
        )

        cls.validated_process.status = Process.Status.VALIDATED
        cls.validated_process.save()

        cls.draft_process = Process.objects.create(
            name="Draft Process",
            code="PROC-DRF",
            scale="Lab",
            version=1,
        )
        cls.draft_unit_1 = UnitOperation.objects.create(
            process=cls.draft_process,
            name=cls.global_unit_usp.name,
            unit_type=cls.global_unit_usp.unit_type,
            order=1,
        )
        cls.draft_unit_2 = UnitOperation.objects.create(
            process=cls.draft_process,
            name=cls.global_unit_dsp.name,
            unit_type=cls.global_unit_dsp.unit_type,
            order=2,
        )
        cls.archived_unit = UnitOperation.objects.create(
            process=cls.draft_process,
            name="Archived Unit",
            unit_type="USP",
            order=100,
        )
        cls.archived_unit.delete(user=cls.admin)

        cls.draft_step_1 = Step.objects.create(
            unit_operation=cls.draft_unit_1,
            name="Draft Step 1",
            order=1,
        )
        cls.draft_step_2 = Step.objects.create(
            unit_operation=cls.draft_unit_1,
            name="Draft Step 2",
            order=2,
        )
        cls.archived_step = Step.objects.create(
            unit_operation=cls.draft_unit_1,
            name="Archived Step",
            order=100,
        )
        cls.archived_step.delete(user=cls.admin)

        cls.draft_parameter_1 = Parameter.objects.create(
            step=cls.draft_step_1,
            name="pH",
            unit="pH",
            format_type="numeric",
            format_low_range=5.0,
            format_high_range=7.0,
            order=1,
        )
        cls.draft_parameter_2 = Parameter.objects.create(
            step=cls.draft_step_1,
            name="Conductivity",
            unit="mS/cm",
            format_type="numeric",
            format_low_range=1.0,
            format_high_range=3.0,
            order=2,
        )
        cls.archived_parameter = Parameter.objects.create(
            step=cls.draft_step_1,
            name="Archived Param",
            unit="u",
            format_type="numeric",
            format_low_range=0.0,
            format_high_range=1.0,
            order=100,
        )
        cls.archived_parameter.delete(user=cls.admin)

        cls.draft_sample_1 = Sample.objects.create(step=cls.draft_step_1, name="Sample 1")
        cls.draft_sample_2 = Sample.objects.create(step=cls.draft_step_1, name="Sample 2")
        cls.archived_sample = Sample.objects.create(step=cls.draft_step_1, name="Archived Sample")
        cls.archived_sample.delete(user=cls.admin)

        cls.draft_analysis_1 = Analysis.objects.create(
            sample=cls.draft_sample_1,
            analysis_name="Assay 1",
            analytical_method=cls.method,
            format_low_range=0.0,
            format_high_range=10.0,
        )
        cls.draft_analysis_2 = Analysis.objects.create(
            sample=cls.draft_sample_1,
            analysis_name="Assay 2",
            analytical_method=cls.method,
            format_low_range=0.0,
            format_high_range=10.0,
        )
        cls.archived_analysis = Analysis.objects.create(
            sample=cls.draft_sample_1,
            analysis_name="Archived Assay",
            analytical_method=cls.method,
            format_low_range=0.0,
            format_high_range=10.0,
        )
        cls.archived_analysis.delete(user=cls.admin)

        cls.pending_process = Process.objects.create(
            name="Pending Process",
            code="PROC-PEN",
            scale="Pilot",
            version=1,
            status=Process.Status.PENDING,
        )
        cls.rejected_process = Process.objects.create(
            name="Rejected Process",
            code="PROC-REJ",
            scale="Pilot",
            version=1,
            status=Process.Status.REJECTED,
        )

    def _build_process_request_data(self, process):
        return {
            "name": process.name,
            "code": process.code,
            "scale": process.scale,
        }


class ProductionModelTests(ProductionTestDataMixin, TestCase):
    def test_string_representations(self):
        self.assertEqual(str(self.validated_process), "PROC-VAL v1 (Pilot)")
        self.assertEqual(str(self.validated_unit), f"{self.global_unit_usp.name} ({self.global_unit_usp.unit_type})")
        self.assertEqual(str(self.validated_step), "USP Granulation -> Mixing (#1)")
        self.assertEqual(str(self.validated_parameter), "Temperature (Mixing)")
        self.assertEqual(str(self.validated_sample), "Sample 'Sample A' for Mixing")
        self.assertEqual(str(self.validated_analysis), "Potency -> HPLC")

    def test_process_unique_version_per_code(self):
        with self.assertRaises(ValidationError):
            Process.objects.create(
                name="Duplicate Process",
                code=self.validated_process.code,
                scale="Pilot",
                version=1,
            )

    def test_parameter_numeric_validation(self):
        with self.assertRaises(ValidationError):
            Parameter.objects.create(
                step=self.validated_step,
                name="Missing Bounds",
                unit="C",
                format_type="numeric",
                order=9,
            )

        with self.assertRaises(ValidationError):
            Parameter.objects.create(
                step=self.validated_step,
                name="Invalid Bounds",
                unit="C",
                format_type="numeric",
                format_low_range=10.0,
                format_high_range=5.0,
                order=10,
            )

    def test_parameter_non_numeric_clears_ranges(self):
        param = Parameter.objects.create(
            step=self.validated_step,
            name="Comment",
            unit="text",
            format_type="text",
            format_low_range=1.0,
            format_high_range=2.0,
            order=11,
        )
        self.assertIsNone(param.format_low_range)
        self.assertIsNone(param.format_high_range)

    def test_analysis_validation(self):
        with self.assertRaises(ValidationError):
            Analysis.objects.create(
                sample=self.validated_sample,
                analysis_name="Invalid ranges",
                analytical_method=self.method,
                format_low_range=5.0,
                format_high_range=1.0,
            )

    def test_edit_url_rules(self):
        self.assertIsNone(self.validated_process.edit_url)
        self.assertIsNone(self.validated_unit.edit_url)


class ProductionFormTests(ProductionTestDataMixin, TestCase):
    def test_process_form_valid(self):
        form = ProcessForm(data={"name": "New Process", "code": "PROC-NEW", "scale": "Lab"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_unit_operation_form_filters_catalog(self):
        form = UnitOperationForm()
        unit_names = set(form.fields["name"].queryset.values_list("name", flat=True))
        self.assertIn(self.global_unit_usp.name, unit_names)
        self.assertIn(self.global_unit_dsp.name, unit_names)
        self.assertNotIn(self.archived_method.name, unit_names)

    def test_step_form_valid(self):
        form = StepForm(instance=Step(unit_operation=self.draft_unit_1), data={"name": "Granulation"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_parameter_form_validates_numeric_ranges(self):
        form = ParameterForm(
            instance=Parameter(step=self.draft_step_1),
            data={
                "name": "pH",
                "unit": "pH",
                "format_type": "numeric",
                "format_low_range": "",
                "format_high_range": "",
                "low_proven_acceptable_range": "",
                "high_proven_acceptable_range": "",
                "low_normal_operating_range": "",
                "high_normal_operating_range": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("format_low_range", form.errors)
        self.assertIn("format_high_range", form.errors)

        text_form = ParameterForm(
            instance=Parameter(step=self.draft_step_1),
            data={
                "name": "Comment",
                "unit": "text",
                "format_type": "text",
                "format_low_range": "2",
                "format_high_range": "4",
                "low_proven_acceptable_range": "1",
                "high_proven_acceptable_range": "5",
                "low_normal_operating_range": "1",
                "high_normal_operating_range": "5",
            }
        )
        self.assertTrue(text_form.is_valid(), text_form.errors)
        self.assertIsNone(text_form.cleaned_data["format_low_range"])
        self.assertIsNone(text_form.cleaned_data["format_high_range"])
        self.assertIsNone(text_form.cleaned_data["low_proven_acceptable_range"])

    def test_sample_and_analysis_forms_valid(self):
        sample_form = SampleForm(instance=Sample(step=self.draft_step_1), data={"name": "Sample X"})
        analysis_form = AnalysisForm(
            instance=Analysis(sample=self.draft_sample_1),
            data={
                "analysis_name": "Potency",
                "analytical_method": self.method.pk,
                "low_normal_operating_range": "",
                "high_normal_operating_range": "",
                "format_low_range": "0",
                "format_high_range": "10",
            }
        )
        self.assertTrue(sample_form.is_valid(), sample_form.errors)
        self.assertTrue(analysis_form.is_valid(), analysis_form.errors)


class ProductionUrlTests(ProductionTestDataMixin, TestCase):
    def test_all_production_urls_reverse(self):
        routes = [
            ("production:process_list", {}),
            ("production:process_add", {}),
            ("production:process_detail", {"pk": self.validated_process.pk}),
            ("production:process_edit", {"pk": self.validated_process.pk}),
            ("production:process_delete", {"pk": self.validated_process.pk}),
            ("production:process_restore", {"pk": self.validated_process.pk}),
            ("production:process_submit", {"pk": self.validated_process.pk}),
            ("production:process_validate", {"pk": self.validated_process.pk}),
            ("production:process_reject", {"pk": self.validated_process.pk}),
            ("production:process_versioning", {"pk": self.validated_process.pk}),
            ("production:unitoperation_list", {"process_pk": self.draft_process.pk}),
            ("production:unitoperation_add", {"process_pk": self.draft_process.pk}),
            ("production:unitoperation_edit", {"pk": self.draft_unit_1.pk}),
            ("production:unitoperation_delete", {"pk": self.draft_unit_1.pk}),
            ("production:unitoperation_restore", {"pk": self.draft_unit_1.pk}),
            ("production:unitoperation_reorder", {"pk": self.draft_unit_1.pk, "direction": "up"}),
            ("production:unitoperation_detail", {"pk": self.draft_unit_1.pk}),
            ("production:step_list", {"unit_pk": self.draft_unit_1.pk}),
            ("production:step_add", {"unit_pk": self.draft_unit_1.pk}),
            ("production:step_edit", {"pk": self.draft_step_1.pk}),
            ("production:step_delete", {"pk": self.draft_step_1.pk}),
            ("production:step_restore", {"pk": self.draft_step_1.pk}),
            ("production:step_reorder", {"pk": self.draft_step_1.pk, "direction": "up"}),
            ("production:step_detail", {"pk": self.draft_step_1.pk}),
            ("production:parameter_list", {"step_pk": self.draft_step_1.pk}),
            ("production:parameter_add", {"step_pk": self.draft_step_1.pk}),
            ("production:parameter_edit", {"pk": self.draft_parameter_1.pk}),
            ("production:parameter_delete", {"pk": self.draft_parameter_1.pk}),
            ("production:parameter_restore", {"pk": self.draft_parameter_1.pk}),
            ("production:parameter_reorder", {"pk": self.draft_parameter_1.pk, "direction": "up"}),
            ("production:parameter_detail", {"pk": self.draft_parameter_1.pk}),
            ("production:sample_list", {"step_pk": self.draft_step_1.pk}),
            ("production:sample_add", {"step_pk": self.draft_step_1.pk}),
            ("production:sample_edit", {"pk": self.draft_sample_1.pk}),
            ("production:sample_delete", {"pk": self.draft_sample_1.pk}),
            ("production:sample_restore", {"pk": self.draft_sample_1.pk}),
            ("production:sample_detail", {"pk": self.draft_sample_1.pk}),
            ("production:analysis_list", {"sample_pk": self.draft_sample_1.pk}),
            ("production:analysis_add", {"sample_pk": self.draft_sample_1.pk}),
            ("production:analysis_edit", {"pk": self.draft_analysis_1.pk}),
            ("production:analysis_delete", {"pk": self.draft_analysis_1.pk}),
            ("production:analysis_restore", {"pk": self.draft_analysis_1.pk}),
            ("production:analysis_detail", {"pk": self.draft_analysis_1.pk}),
        ]

        for route_name, kwargs in routes:
            with self.subTest(route_name=route_name):
                self.assertTrue(reverse(route_name, kwargs=kwargs).startswith("/production/"))


class ProductionSecurityTests(ProductionTestDataMixin, TestCase):
    def assert_status(self, method, url_name, user, expected_status, kwargs=None, data=None):
        self.client.force_login(user)
        kwargs = kwargs or {}
        data = data or {}
        response = getattr(self.client, method)(reverse(url_name, kwargs=kwargs), data)
        self.assertEqual(response.status_code, expected_status)

    def test_anonymous_users_are_redirected(self):
        response = self.client.get(reverse("production:process_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_data_steward_permissions(self):
        self.assert_status("get", "production:process_list", self.steward, 200)
        self.assert_status("get", "production:process_detail", self.steward, 200, kwargs={"pk": self.validated_process.pk})
        self.assert_status("post", "production:process_validate", self.steward, 403, kwargs={"pk": self.pending_process.pk})
        self.assert_status("post", "production:process_reject", self.steward, 403, kwargs={"pk": self.pending_process.pk}, data={"rejection_reason": "No"})

    def test_qa_permissions(self):
        self.assert_status("get", "production:process_list", self.qa, 200)
        self.assert_status("get", "production:unitoperation_list", self.qa, 200, kwargs={"process_pk": self.draft_process.pk})
        self.assert_status("post", "production:process_edit", self.qa, 403, kwargs={"pk": self.draft_process.pk}, data={})
        self.assert_status("post", "production:unitoperation_add", self.qa, 302, kwargs={"process_pk": self.draft_process.pk}, data={})

    def test_admin_bypass(self):
        self.assert_status("get", "production:process_add", self.admin, 200)
        self.assert_status("post", "production:process_validate", self.admin, 302, kwargs={"pk": self.pending_process.pk})
        self.assert_status("post", "production:process_reject", self.admin, 302, kwargs={"pk": self.rejected_process.pk}, data={"rejection_reason": "Admin review"})


class ProductionWorkflowTests(ProductionTestDataMixin, TestCase):
    def test_process_list_counts_and_search(self):
        self.client.force_login(self.steward)

        response = self.client.get(reverse("production:process_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["view_mode"], "draft")
        self.assertEqual(response.context["count_draft"], 1)
        self.assertEqual(response.context["count_pending"], 1)
        self.assertEqual(response.context["count_active"], 1)
        self.assertEqual(response.context["count_rejected"], 1)
        self.assertEqual(response.context["processes"].count(), 1)

        search_response = self.client.get(reverse("production:process_list"), {"q": "PROC-DRF"})
        self.assertEqual(search_response.status_code, 200)
        self.assertEqual(search_response.context["processes"].count(), 1)

    def test_process_submit_validate_and_reject(self):
        self.client.force_login(self.admin)

        submit_response = self.client.post(reverse("production:process_submit", kwargs={"pk": self.draft_process.pk}))
        self.assertEqual(submit_response.status_code, 302)
        self.draft_process.refresh_from_db()
        self.assertEqual(self.draft_process.status, Process.Status.PENDING)
        self.assertEqual(self.draft_process.updated_by, self.admin)

        validate_response = self.client.post(reverse("production:process_validate", kwargs={"pk": self.pending_process.pk}))
        self.assertEqual(validate_response.status_code, 302)
        self.pending_process.refresh_from_db()
        self.assertEqual(self.pending_process.status, Process.Status.VALIDATED)
        self.assertEqual(self.pending_process.updated_by, self.admin)

        reject_response = self.client.post(
            reverse("production:process_reject", kwargs={"pk": self.rejected_process.pk}),
            data={"rejection_reason": "Needs correction"},
        )
        self.assertEqual(reject_response.status_code, 302)
        self.rejected_process.refresh_from_db()
        self.assertEqual(self.rejected_process.status, Process.Status.REJECTED)

    def test_process_update_and_delete_locked_when_pending(self):
        self.client.force_login(self.admin)

        update_response = self.client.post(
            reverse("production:process_edit", kwargs={"pk": self.pending_process.pk}),
            data=self._build_process_request_data(self.pending_process),
        )
        self.assertEqual(update_response.status_code, 302)
        self.assertEqual(update_response.url, reverse("production:process_list"))

        delete_response = self.client.post(reverse("production:process_delete", kwargs={"pk": self.pending_process.pk}))
        self.assertEqual(delete_response.status_code, 302)
        self.assertEqual(delete_response.url, reverse("production:process_list"))

    def test_process_update_delete_restore_on_draft(self):
        self.client.force_login(self.steward)

        update_response = self.client.post(
            reverse("production:process_edit", kwargs={"pk": self.draft_process.pk}),
            data={
                "name": "Draft Process Updated",
                "code": self.draft_process.code,
                "scale": self.draft_process.scale,
                "change_justification": "Naming correction",
            },
        )
        self.assertEqual(update_response.status_code, 302)
        self.draft_process.refresh_from_db()
        self.assertEqual(self.draft_process.name, "Draft Process Updated")
        self.assertEqual(self.draft_process.updated_by, self.steward)

        delete_response = self.client.post(reverse("production:process_delete", kwargs={"pk": self.draft_process.pk}))
        self.assertEqual(delete_response.status_code, 302)
        self.draft_process.refresh_from_db()
        self.assertFalse(self.draft_process.is_active)
        self.assertEqual(self.draft_process.deleted_by, self.steward)

        restore_response = self.client.post(reverse("production:process_restore", kwargs={"pk": self.draft_process.pk}))
        self.assertEqual(restore_response.status_code, 302)
        self.draft_process.refresh_from_db()
        self.assertTrue(self.draft_process.is_active)
        self.assertEqual(self.draft_process.status, Process.Status.DRAFT)

    def test_process_versioning_clones_structure(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse("production:process_versioning", kwargs={"pk": self.validated_process.pk}))
        self.assertEqual(response.status_code, 302)

        new_process = Process.objects.get(code=self.validated_process.code, version=2)
        self.assertEqual(new_process.parent_version, self.validated_process)
        self.assertEqual(new_process.status, Process.Status.DRAFT)
        self.assertEqual(new_process.units.count(), 1)

        cloned_unit = new_process.units.first()
        self.assertEqual(cloned_unit.steps.count(), 1)
        cloned_step = cloned_unit.steps.first()
        self.assertEqual(cloned_step.parameters.count(), 1)
        self.assertEqual(cloned_step.samples.count(), 1)
        self.assertEqual(cloned_step.samples.first().analyses.count(), 1)

    def test_unit_structure_add_reorder_restore_and_detail(self):
        self.client.force_login(self.steward)

        response = self.client.get(reverse("production:unitoperation_list", kwargs={"process_pk": self.draft_process.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["count_active"], 2)
        self.assertEqual(response.context["count_archived"], 1)
        self.assertEqual(response.context["user_group"], "Data_Steward")

        add_response = self.client.post(
            reverse("production:unitoperation_add", kwargs={"process_pk": self.draft_process.pk}),
            data={"name": self.global_unit_usp.name},
        )
        self.assertEqual(add_response.status_code, 302)
        added_unit = UnitOperation.objects.get(process=self.draft_process, order=3, name=self.global_unit_usp.name)
        self.assertEqual(added_unit.created_by, self.steward)

        reorder_response = self.client.get(
            reverse("production:unitoperation_reorder", kwargs={"pk": self.draft_unit_1.pk, "direction": "down"})
        )
        self.assertEqual(reorder_response.status_code, 302)
        self.draft_unit_1.refresh_from_db()
        self.draft_unit_2.refresh_from_db()
        self.assertEqual(self.draft_unit_1.order, 2)
        self.assertEqual(self.draft_unit_2.order, 1)

        detail_response = self.client.get(reverse("production:unitoperation_detail", kwargs={"pk": self.draft_unit_1.pk}))
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.context["dynamic_actions"], [])

        restore_response = self.client.post(reverse("production:unitoperation_restore", kwargs={"pk": self.archived_unit.pk}))
        self.assertEqual(restore_response.status_code, 302)
        self.archived_unit.refresh_from_db()
        self.assertTrue(self.archived_unit.is_active)

    def test_step_structure_add_reorder_restore_and_detail(self):
        self.client.force_login(self.steward)

        response = self.client.get(reverse("production:step_list", kwargs={"unit_pk": self.draft_unit_1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["count_active"], 2)
        self.assertEqual(response.context["count_archived"], 1)

        add_response = self.client.post(
            reverse("production:step_add", kwargs={"unit_pk": self.draft_unit_1.pk}),
            data={"name": "Draft Step 3"},
        )
        self.assertEqual(add_response.status_code, 302)
        added_step = Step.objects.get(unit_operation=self.draft_unit_1, name="Draft Step 3")
        self.assertEqual(added_step.created_by, self.steward)

        reorder_response = self.client.get(
            reverse("production:step_reorder", kwargs={"pk": self.draft_step_1.pk, "direction": "down"})
        )
        self.assertEqual(reorder_response.status_code, 302)
        self.draft_step_1.refresh_from_db()
        self.draft_step_2.refresh_from_db()
        self.assertEqual(self.draft_step_1.order, 2)
        self.assertEqual(self.draft_step_2.order, 1)

        detail_response = self.client.get(reverse("production:step_detail", kwargs={"pk": self.draft_step_1.pk}))
        self.assertEqual(detail_response.status_code, 200)

        restore_response = self.client.post(reverse("production:step_restore", kwargs={"pk": self.archived_step.pk}))
        self.assertEqual(restore_response.status_code, 302)
        self.archived_step.refresh_from_db()
        self.assertTrue(self.archived_step.is_active)

    def test_parameter_structure_add_reorder_restore_and_detail(self):
        self.client.force_login(self.steward)

        response = self.client.get(reverse("production:parameter_list", kwargs={"step_pk": self.draft_step_1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["count_active"], 2)
        self.assertEqual(response.context["count_archived"], 1)

        add_response = self.client.post(
            reverse("production:parameter_add", kwargs={"step_pk": self.draft_step_1.pk}),
            data={
                "name": "Pressure",
                "unit": "bar",
                "format_type": "numeric",
                "format_low_range": 1,
                "format_high_range": 5,
                "low_proven_acceptable_range": "",
                "high_proven_acceptable_range": "",
                "low_normal_operating_range": "",
                "high_normal_operating_range": "",
            },
        )
        self.assertEqual(add_response.status_code, 302)
        added_param = Parameter.objects.get(step=self.draft_step_1, name="Pressure")
        self.assertEqual(added_param.created_by, self.steward)

        reorder_response = self.client.get(
            reverse("production:parameter_reorder", kwargs={"pk": self.draft_parameter_1.pk, "direction": "down"})
        )
        self.assertEqual(reorder_response.status_code, 302)
        self.draft_parameter_1.refresh_from_db()
        self.draft_parameter_2.refresh_from_db()
        self.assertEqual(self.draft_parameter_1.order, 2)
        self.assertEqual(self.draft_parameter_2.order, 1)

        detail_response = self.client.get(reverse("production:parameter_detail", kwargs={"pk": self.draft_parameter_1.pk}))
        self.assertEqual(detail_response.status_code, 200)

        restore_response = self.client.post(
            reverse("production:parameter_restore", kwargs={"pk": self.archived_parameter.pk})
        )
        self.assertEqual(restore_response.status_code, 302)
        self.archived_parameter.refresh_from_db()
        self.assertTrue(self.archived_parameter.is_active)

    def test_sample_structure_add_restore_and_detail(self):
        self.client.force_login(self.steward)

        response = self.client.get(reverse("production:sample_list", kwargs={"step_pk": self.draft_step_1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["count_active"], 2)
        self.assertEqual(response.context["count_archived"], 1)

        add_response = self.client.post(
            reverse("production:sample_add", kwargs={"step_pk": self.draft_step_1.pk}),
            data={"name": "Sample 3"},
        )
        self.assertEqual(add_response.status_code, 302)
        added_sample = Sample.objects.get(step=self.draft_step_1, name="Sample 3")
        self.assertEqual(added_sample.created_by, self.steward)

        detail_response = self.client.get(reverse("production:sample_detail", kwargs={"pk": self.draft_sample_1.pk}))
        self.assertEqual(detail_response.status_code, 200)

        restore_response = self.client.post(reverse("production:sample_restore", kwargs={"pk": self.archived_sample.pk}))
        self.assertEqual(restore_response.status_code, 302)
        self.archived_sample.refresh_from_db()
        self.assertTrue(self.archived_sample.is_active)

    def test_analysis_structure_add_restore_and_detail(self):
        self.client.force_login(self.steward)

        response = self.client.get(reverse("production:analysis_list", kwargs={"sample_pk": self.draft_sample_1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["count_active"], 2)
        self.assertEqual(response.context["count_archived"], 1)

        add_response = self.client.post(
            reverse("production:analysis_add", kwargs={"sample_pk": self.draft_sample_1.pk}),
            data={
                "analysis_name": "Assay 3",
                "analytical_method": self.method.pk,
                "low_normal_operating_range": "",
                "high_normal_operating_range": "",
                "format_low_range": 0,
                "format_high_range": 10,
            },
        )
        self.assertEqual(add_response.status_code, 302)
        added_analysis = Analysis.objects.get(sample=self.draft_sample_1, analysis_name="Assay 3")
        self.assertEqual(added_analysis.created_by, self.steward)

        detail_response = self.client.get(reverse("production:analysis_detail", kwargs={"pk": self.draft_analysis_1.pk}))
        self.assertEqual(detail_response.status_code, 200)

        restore_response = self.client.post(
            reverse("production:analysis_restore", kwargs={"pk": self.archived_analysis.pk})
        )
        self.assertEqual(restore_response.status_code, 302)
        self.archived_analysis.refresh_from_db()
        self.assertTrue(self.archived_analysis.is_active)
