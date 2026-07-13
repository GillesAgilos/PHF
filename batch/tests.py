from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from production.models import Analysis, Parameter, Process, Sample, Step, UnitOperation
from referential.models import AnalyticalMethod, Client, MoleculeType, Project

from .forms import AnalysisResultForm, BatchForm, ParameterResultForm
from .models import AnalysisResult, Batch, ParameterResult
from .views import AnalysisResultListView, ParameterResultListView


class BatchTestDataMixin:

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        cls.system_admin_group = Group.objects.create(name="System_Admin")
        cls.data_custodian_group = Group.objects.create(name="Data_Custodian")
        cls.data_steward_group = Group.objects.create(name="Data_Steward")
        cls.qa_group = Group.objects.create(name="QA")
        cls.data_investigator_group = Group.objects.create(name="Data_Investigator")

        cls.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass12345",
            is_staff=True,
            is_superuser=True,
        )
        cls.custodian = User.objects.create_user(
            username="custodian",
            email="custodian@example.com",
            password="pass12345",
            is_staff=True,
        )
        cls.custodian.groups.add(cls.data_custodian_group)

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

        cls.investigator = User.objects.create_user(
            username="investigator",
            email="investigator@example.com",
            password="pass12345",
            is_staff=True,
        )
        cls.investigator.groups.add(cls.data_investigator_group)

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
        cls.draft_project = Project.objects.create(
            code="PRJ-002",
            molecule_name="Molecule B",
            client=cls.client_entity,
            molecule_type=cls.molecule_type,
        )

        cls.method = AnalyticalMethod.objects.create(
            name="HPLC",
            unit="mg/L",
            sop_code="SOP-001",
            sop_version="v1",
            status=AnalyticalMethod.Status.VALIDATED,
        )

        cls.process = Process.objects.create(
            name="Main Process",
            code="PROC-001",
            scale="Pilot",
        )
        cls.unit = UnitOperation.objects.create(
            process=cls.process,
            name="USP Unit",
            unit_type="USP",
            order=1,
        )
        cls.step = Step.objects.create(
            unit_operation=cls.unit,
            name="Step 1",
            order=1,
        )
        cls.parameter = Parameter.objects.create(
            step=cls.step,
            name="pH",
            format_type="numeric",
            order=1,
            unit="pH",
            format_lower_range=5.0,
            format_upper_range=7.0,
        )
        cls.sample = Sample.objects.create(
            step=cls.step,
            name="Sample 1",
        )
        cls.analysis = Analysis.objects.create(
            sample=cls.sample,
            analysis_name="Potency",
            analytical_method=cls.method,
            format_lower_range=0.0,
            format_upper_range=10.0,
        )

        cls.archived_parameter = Parameter.objects.create(
            step=cls.step,
            name="Archived pH",
            format_type="numeric",
            order=2,
            unit="pH",
            format_lower_range=5.0,
            format_upper_range=7.0,
        )
        cls.archived_parameter.delete(user=cls.admin)

        cls.archived_analysis = Analysis.objects.create(
            sample=cls.sample,
            analysis_name="Archived Potency",
            analytical_method=cls.method,
            format_lower_range=0.0,
            format_upper_range=10.0,
        )
        cls.archived_analysis.delete(user=cls.admin)

        cls.bool_process = Process.objects.create(
            name="Aux Process",
            code="PROC-002",
            scale="Lab",
        )
        cls.bool_unit = UnitOperation.objects.create(
            process=cls.bool_process,
            name="DSP Unit",
            unit_type="DSP",
            order=1,
        )
        cls.bool_step = Step.objects.create(
            unit_operation=cls.bool_unit,
            name="Aux Step",
            order=1,
        )
        cls.bool_parameter = Parameter.objects.create(
            step=cls.bool_step,
            name="Visibility",
            format_type="bool",
            order=1,
            unit="n/a",
        )

        cls.process.status = Process.Status.VALIDATED
        cls.process.save()

        cls.batch1 = Batch.objects.create(
            name="Batch 001",
            project=cls.project,
            process=cls.process,
            category=Batch.CategoryChoices.MANUFACTURING,
            iteration_number=1,
        )
        cls.batch2 = Batch.objects.create(
            name="Batch 002",
            project=cls.project,
            process=cls.process,
            category=Batch.CategoryChoices.MANUFACTURING,
            iteration_number=2,
        )
        cls.batch_rejected = Batch.objects.create(
            name="Batch 003",
            project=cls.project,
            process=cls.process,
            category=Batch.CategoryChoices.MANUFACTURING,
            iteration_number=3,
            status=Batch.Status.REJECTED,
        )
        cls.batch_archived = Batch.objects.create(
            name="Batch 004",
            project=cls.project,
            process=cls.process,
            category=Batch.CategoryChoices.MANUFACTURING,
            iteration_number=4,
        )
        cls.batch_archived.delete(user=cls.admin)

        cls.parameter_result = ParameterResult.objects.create(
            batch=cls.batch1,
            parameter=cls.parameter,
            actual_value="5",
        )
        cls.analysis_result = AnalysisResult.objects.create(
            batch=cls.batch1,
            analysis=cls.analysis,
            actual_value="5",
        )


class BatchModelTests(BatchTestDataMixin, TestCase):
    def test_string_representations(self):
        self.assertEqual(str(self.batch1), "M- Lot (Iter: 1)")
        self.assertEqual(str(self.parameter_result), "Batch 001 - pH: 5")
        self.assertEqual(str(self.analysis_result), "Batch 001 - Potency: 5")

    def test_batch_validation_fails_when_results_are_missing(self):
        with self.assertRaises(ValidationError):
            self.batch2.validate_entity(user=self.steward)

    def test_batch_validation_succeeds_when_results_are_complete(self):
        self.batch1.validate_entity(user=self.steward)
        self.batch1.refresh_from_db()

        self.assertEqual(self.batch1.status, Batch.Status.VALIDATED)
        self.assertEqual(self.batch1.updated_by, self.steward)

    def test_parameter_result_validation_rules(self):
        with self.assertRaises(ValidationError):
            ParameterResult.objects.create(
                batch=self.batch2,
                parameter=self.parameter,
            )

        with self.assertRaises(ValidationError):
            ParameterResult.objects.create(
                batch=self.batch2,
                parameter=self.parameter,
                actual_value="99",
            )

    def test_analysis_result_validation_rules(self):
        with self.assertRaises(ValidationError):
            AnalysisResult.objects.create(
                batch=self.batch2,
                analysis=self.analysis,
            )

        with self.assertRaises(ValidationError):
            AnalysisResult.objects.create(
                batch=self.batch2,
                analysis=self.analysis,
                actual_value="99",
            )


class BatchFormTests(BatchTestDataMixin, TestCase):
    def test_batch_form_filters_related_querysets_and_initial_iteration(self):
        form = BatchForm(data={"project": self.project.pk})

        self.assertIn(self.project.pk, set(form.fields["project"].queryset.values_list("pk", flat=True)))
        self.assertNotIn(self.draft_project.pk, set(form.fields["project"].queryset.values_list("pk", flat=True)))
        self.assertIn(self.process.pk, set(form.fields["process"].queryset.values_list("pk", flat=True)))
        self.assertNotIn(self.bool_process.pk, set(form.fields["process"].queryset.values_list("pk", flat=True)))
        self.assertEqual(form.fields["iteration_number"].initial, 4)

    def test_batch_form_rejects_duplicate_iteration_for_same_project(self):
        form = BatchForm(
            data={
                "name": "Duplicate Batch",
                "project": self.project.pk,
                "process": self.process.pk,
                "category": Batch.CategoryChoices.MANUFACTURING,
                "iteration_number": 1,
                "start_date": "",
                "end_date": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("iteration_number", form.errors)

    def test_batch_update_form_marks_related_fields_readonly(self):
        form = BatchForm(instance=self.batch1)

        self.assertEqual(form.fields["project"].widget.attrs.get("readonly"), True)
        self.assertEqual(form.fields["process"].widget.attrs.get("readonly"), True)
        self.assertEqual(form.fields["category"].widget.attrs.get("readonly"), True)

    def test_result_forms_filter_querysets_and_bool_widget(self):
        parameter_form = ParameterResultForm()
        analysis_form = AnalysisResultForm()
        bool_form = ParameterResultForm(initial={"parameter": self.bool_parameter.pk})

        batch_ids = set(parameter_form.fields["batch"].queryset.values_list("pk", flat=True))
        parameter_ids = set(parameter_form.fields["parameter"].queryset.values_list("pk", flat=True))
        analysis_batch_ids = set(analysis_form.fields["batch"].queryset.values_list("pk", flat=True))
        analysis_ids = set(analysis_form.fields["analysis"].queryset.values_list("pk", flat=True))

        self.assertIn(self.batch1.pk, batch_ids)
        self.assertIn(self.batch2.pk, batch_ids)
        self.assertNotIn(self.batch_archived.pk, batch_ids)
        self.assertIn(self.parameter.pk, parameter_ids)
        self.assertIn(self.analysis.pk, analysis_ids)
        self.assertNotIn(self.batch_archived.pk, analysis_batch_ids)
        self.assertIsInstance(bool_form.fields["actual_value"].widget, forms.Select)


class BatchUrlTests(BatchTestDataMixin, TestCase):
    def test_all_batch_urls_reverse(self):
        route_cases = [
            ("batch:batch_list", {}),
            ("batch:batch_add", {}),
            ("batch:batch_detail", {"pk": self.batch1.pk}),
            ("batch:batch_edit", {"pk": self.batch1.pk}),
            ("batch:batch_delete", {"pk": self.batch1.pk}),
            ("batch:batch_restore", {"pk": self.batch1.pk}),
            ("batch:batch_validate", {"pk": self.batch1.pk}),
            ("batch:batch_reject", {"pk": self.batch1.pk}),
            ("batch:batch_logbook", {"pk": self.batch1.pk}),
            ("batch:parameter_result_list", {}),
            ("batch:parameter_result_add", {}),
            ("batch:parameter_result_detail", {"pk": self.parameter_result.pk}),
            ("batch:parameter_result_edit", {"pk": self.parameter_result.pk}),
            ("batch:parameter_result_delete", {"pk": self.parameter_result.pk}),
            ("batch:parameter_result_restore", {"pk": self.parameter_result.pk}),
            ("batch:parameter_result_validate", {"pk": self.parameter_result.pk}),
            ("batch:parameter_result_reject", {"pk": self.parameter_result.pk}),
            ("batch:analysis_result_list", {}),
            ("batch:analysis_result_add", {}),
            ("batch:analysis_result_detail", {"pk": self.analysis_result.pk}),
            ("batch:analysis_result_edit", {"pk": self.analysis_result.pk}),
            ("batch:analysis_result_delete", {"pk": self.analysis_result.pk}),
            ("batch:analysis_result_restore", {"pk": self.analysis_result.pk}),
            ("batch:analysis_result_validate", {"pk": self.analysis_result.pk}),
            ("batch:analysis_result_reject", {"pk": self.analysis_result.pk}),
            ("batch:get_next_iteration", {}),
        ]

        for route_name, kwargs in route_cases:
            with self.subTest(route_name=route_name):
                self.assertTrue(reverse(route_name, kwargs=kwargs).startswith("/batch/"))


class BatchSecurityTests(BatchTestDataMixin, TestCase):
    def assert_status(self, method, url_name, user, expected_status, kwargs=None, data=None):
        self.client.force_login(user)
        kwargs = kwargs or {}
        data = data or {}
        response = getattr(self.client, method)(reverse(url_name, kwargs=kwargs), data)
        self.assertEqual(response.status_code, expected_status)

    def test_anonymous_users_are_redirected_to_login(self):
        response = self.client.get(reverse("batch:batch_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_data_custodian_permissions(self):
        self.assert_status("get", "batch:batch_list", self.custodian, 200)
        self.assert_status("get", "batch:batch_detail", self.custodian, 200, kwargs={"pk": self.batch1.pk})
        self.assert_status("get", "batch:batch_logbook", self.custodian, 200, kwargs={"pk": self.batch1.pk})
        self.assert_status("get", "batch:batch_add", self.custodian, 403)
        self.assert_status("get", "batch:batch_edit", self.custodian, 403, kwargs={"pk": self.batch2.pk})
        self.assert_status("post", "batch:batch_delete", self.custodian, 403, kwargs={"pk": self.batch2.pk})
        self.assert_status("post", "batch:batch_restore", self.custodian, 403, kwargs={"pk": self.batch2.pk})
        self.assert_status("post", "batch:batch_validate", self.custodian, 403, kwargs={"pk": self.batch1.pk})
        self.assert_status("post", "batch:batch_reject", self.custodian, 403, kwargs={"pk": self.batch1.pk}, data={"rejection_reason": "No"})
        self.assert_status("get", "batch:parameter_result_list", self.custodian, 200)
        self.assert_status("get", "batch:analysis_result_list", self.custodian, 200)
        self.assert_status("get", "batch:parameter_result_add", self.custodian, 200)
        self.assert_status("get", "batch:analysis_result_add", self.custodian, 200)
        self.assert_status("post", "batch:parameter_result_validate", self.custodian, 302, kwargs={"pk": self.parameter_result.pk})
        self.assert_status("post", "batch:analysis_result_reject", self.custodian, 302, kwargs={"pk": self.analysis_result.pk}, data={"rejection_reason": "No"})

    def test_data_custodian_templates_hide_batch_actions_but_show_logbook_actions(self):
        self.client.force_login(self.custodian)

        batch_list_response = self.client.get(reverse("batch:batch_list"))
        batch_list_html = batch_list_response.content.decode()
        self.assertNotIn("Instantiate New Batch", batch_list_html)
        self.assertNotIn(reverse("batch:batch_add"), batch_list_html)
        self.assertNotIn(reverse("batch:batch_edit", kwargs={"pk": self.batch1.pk}), batch_list_html)

        logbook_response = self.client.get(reverse("batch:batch_logbook", kwargs={"pk": self.batch1.pk}))
        logbook_html = logbook_response.content.decode()
        self.assertIn(reverse("batch:parameter_result_detail", kwargs={"pk": self.parameter_result.pk}), logbook_html)
        self.assertIn(reverse("batch:analysis_result_detail", kwargs={"pk": self.analysis_result.pk}), logbook_html)
        self.assertIn(reverse("batch:parameter_result_edit", kwargs={"pk": self.parameter_result.pk}), logbook_html)
        self.assertIn(reverse("batch:analysis_result_edit", kwargs={"pk": self.analysis_result.pk}), logbook_html)

    def test_data_custodian_logbook_write_permissions(self):
        self.client.force_login(self.custodian)

        parameter_create_response = self.client.post(
            reverse("batch:parameter_result_add"),
            data={
                "batch": self.batch2.pk,
                "parameter": self.bool_parameter.pk,
                "actual_value": "Yes",
                "comment": "",
            },
        )
        self.assertEqual(parameter_create_response.status_code, 302)

        created_parameter = ParameterResult.objects.get(batch=self.batch2, parameter=self.bool_parameter)
        self.assertEqual(created_parameter.created_by, self.custodian)
        self.assertEqual(created_parameter.updated_by, self.custodian)

        parameter_update_response = self.client.post(
            reverse("batch:parameter_result_edit", kwargs={"pk": created_parameter.pk}),
            data={
                "batch": self.batch2.pk,
                "parameter": self.bool_parameter.pk,
                "actual_value": "No",
                "comment": "",
                "change_justification": "Correction",
            },
        )
        self.assertEqual(parameter_update_response.status_code, 302)

        parameter_delete_response = self.client.post(reverse("batch:parameter_result_delete", kwargs={"pk": created_parameter.pk}))
        self.assertEqual(parameter_delete_response.status_code, 302)

        parameter_restore_response = self.client.post(reverse("batch:parameter_result_restore", kwargs={"pk": created_parameter.pk}))
        self.assertEqual(parameter_restore_response.status_code, 302)

        self.assertTrue(ParameterResult.objects.get(pk=created_parameter.pk).is_active)

        created_analysis = Analysis.objects.create(
            sample=self.sample,
            analysis_name="Impurity",
            analytical_method=self.method,
            format_lower_range=0.0,
            format_upper_range=10.0,
        )

        analysis_create_response = self.client.post(
            reverse("batch:analysis_result_add"),
            data={
                "batch": self.batch2.pk,
                "analysis": created_analysis.pk,
                "actual_value": "5",
                "comment": "",
            },
        )
        self.assertEqual(analysis_create_response.status_code, 302)

        created_analysis_result = AnalysisResult.objects.get(batch=self.batch2, analysis=created_analysis)
        self.assertEqual(created_analysis_result.created_by, self.custodian)
        self.assertEqual(created_analysis_result.updated_by, self.custodian)

        analysis_update_response = self.client.post(
            reverse("batch:analysis_result_edit", kwargs={"pk": created_analysis_result.pk}),
            data={
                "batch": self.batch2.pk,
                "analysis": created_analysis.pk,
                "actual_value": "6",
                "comment": "",
                "change_justification": "Correction",
            },
        )
        self.assertEqual(analysis_update_response.status_code, 302)

        analysis_delete_response = self.client.post(reverse("batch:analysis_result_delete", kwargs={"pk": created_analysis_result.pk}))
        self.assertEqual(analysis_delete_response.status_code, 302)

        analysis_restore_response = self.client.post(reverse("batch:analysis_result_restore", kwargs={"pk": created_analysis_result.pk}))
        self.assertEqual(analysis_restore_response.status_code, 302)

        self.assertTrue(AnalysisResult.objects.get(pk=created_analysis_result.pk).is_active)

    def test_data_steward_permissions(self):
        self.assert_status("get", "batch:batch_list", self.steward, 200)
        self.assert_status("get", "batch:batch_detail", self.steward, 200, kwargs={"pk": self.batch1.pk})
        self.assert_status("get", "batch:batch_logbook", self.steward, 200, kwargs={"pk": self.batch1.pk})
        self.assert_status("get", "batch:batch_add", self.steward, 403)
        self.assert_status("post", "batch:batch_edit", self.steward, 403, kwargs={"pk": self.batch1.pk})
        self.assert_status("post", "batch:batch_validate", self.steward, 302, kwargs={"pk": self.batch1.pk})
        self.assert_status("post", "batch:batch_reject", self.steward, 302, kwargs={"pk": self.batch2.pk}, data={"rejection_reason": "Needs correction"})

    def test_qa_permissions(self):
        self.assert_status("get", "batch:batch_list", self.qa, 200)
        self.assert_status("get", "batch:batch_detail", self.qa, 200, kwargs={"pk": self.batch1.pk})
        self.assert_status("get", "batch:batch_logbook", self.qa, 200, kwargs={"pk": self.batch1.pk})
        self.assert_status("get", "batch:batch_add", self.qa, 403)
        self.assert_status("post", "batch:batch_edit", self.qa, 403, kwargs={"pk": self.batch1.pk})
        self.assert_status("post", "batch:batch_validate", self.qa, 403, kwargs={"pk": self.batch1.pk})
        self.assert_status("post", "batch:batch_reject", self.qa, 403, kwargs={"pk": self.batch1.pk}, data={"rejection_reason": "No"})

    def test_data_investigator_read_only_permissions(self):
        self.assert_status("get", "batch:batch_list", self.investigator, 200)
        self.assert_status("get", "batch:batch_detail", self.investigator, 200, kwargs={"pk": self.batch1.pk})
        self.assert_status("get", "batch:batch_logbook", self.investigator, 200, kwargs={"pk": self.batch1.pk})
        self.assert_status("get", "batch:batch_add", self.investigator, 403)
        self.assert_status("post", "batch:batch_edit", self.investigator, 403, kwargs={"pk": self.batch1.pk})
        self.assert_status("post", "batch:batch_validate", self.investigator, 403, kwargs={"pk": self.batch1.pk})
        self.assert_status("post", "batch:batch_reject", self.investigator, 403, kwargs={"pk": self.batch1.pk}, data={"rejection_reason": "No"})

    def test_admin_bypass(self):
        self.assert_status("get", "batch:batch_add", self.admin, 200)
        self.assert_status("post", "batch:batch_validate", self.admin, 302, kwargs={"pk": self.batch1.pk})
        self.assert_status("post", "batch:batch_reject", self.admin, 302, kwargs={"pk": self.batch2.pk}, data={"rejection_reason": "Admin decision"})


class BatchViewTests(BatchTestDataMixin, TestCase):
    def test_batch_list_counts_and_search(self):
        self.client.force_login(self.steward)

        response = self.client.get(reverse("batch:batch_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["view_mode"], "draft")
        self.assertEqual(response.context["count_draft"], 2)
        self.assertEqual(response.context["count_rejected"], 1)
        self.assertEqual(response.context["count_archived"], 1)
        self.assertEqual(response.context["count_active"], 0)
        self.assertEqual(len(response.context["batches"]), 2)

        search_response = self.client.get(reverse("batch:batch_list"), {"q": "Batch"})
        self.assertEqual(search_response.status_code, 200)
        self.assertEqual(search_response.context["batches"].count(), 2)

    def test_batch_detail_actions_change_with_status(self):
        self.client.force_login(self.steward)

        draft_response = self.client.get(reverse("batch:batch_detail", kwargs={"pk": self.batch1.pk}))
        draft_labels = [action["label"] for action in draft_response.context["dynamic_actions"]]
        self.assertIn("Edit Record", draft_labels)
        self.assertIn("Validate", draft_labels)
        self.assertIn("Reject", draft_labels)

        self.client.post(reverse("batch:batch_validate", kwargs={"pk": self.batch1.pk}))
        self.batch1.refresh_from_db()

        validated_response = self.client.get(reverse("batch:batch_detail", kwargs={"pk": self.batch1.pk}))
        validated_labels = [action["label"] for action in validated_response.context["dynamic_actions"]]
        self.assertNotIn("Edit Record", validated_labels)

    def test_data_custodian_batch_detail_is_read_only(self):
        self.client.force_login(self.custodian)

        response = self.client.get(reverse("batch:batch_detail", kwargs={"pk": self.batch1.pk}))
        labels = [action["label"] for action in response.context["dynamic_actions"]]

        self.assertNotIn("Edit Record", labels)
        self.assertNotIn("Validate", labels)
        self.assertNotIn("Reject", labels)

    def test_batch_logbook_builds_process_tree(self):
        self.client.force_login(self.steward)

        response = self.client.get(reverse("batch:batch_logbook", kwargs={"pk": self.batch1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user_group"], "Data_Steward")
        self.assertEqual(len(response.context["process_tree"]), 1)

        unit_entry = response.context["process_tree"][0]
        self.assertEqual(unit_entry["object"].pk, self.unit.pk)
        self.assertEqual(len(unit_entry["steps"]), 1)

        step_entry = unit_entry["steps"][0]
        self.assertEqual(step_entry["object"].pk, self.step.pk)
        self.assertEqual(len(step_entry["parameters_with_results"]), 1)
        self.assertEqual(step_entry["parameters_with_results"][0]["parameter"].pk, self.parameter.pk)
        self.assertEqual(step_entry["parameters_with_results"][0]["result"].pk, self.parameter_result.pk)
        self.assertEqual(len(step_entry["analyses_with_results"]), 1)
        self.assertEqual(step_entry["analyses_with_results"][0]["analysis"].pk, self.analysis.pk)
        self.assertEqual(step_entry["analyses_with_results"][0]["result"].pk, self.analysis_result.pk)
        self.assertNotIn(self.archived_parameter.name, response.content.decode())
        self.assertNotIn(self.archived_analysis.analysis_name, response.content.decode())

    def test_batch_validation_ignores_archived_process_results(self):
        self.batch1.validate_entity(user=self.steward)
        self.batch1.refresh_from_db()

        self.assertEqual(self.batch1.status, Batch.Status.VALIDATED)

    def test_batch_create_update_delete_restore_flow(self):
        self.client.force_login(self.admin)

        create_response = self.client.post(
            reverse("batch:batch_add"),
            data={
                "name": "Batch 005",
                "project": self.project.pk,
                "process": self.process.pk,
                "category": Batch.CategoryChoices.MANUFACTURING,
                "iteration_number": 5,
                "start_date": "",
                "end_date": "",
            },
        )
        self.assertEqual(create_response.status_code, 302)

        created_batch = Batch.objects.get(name="Batch 005")
        self.assertEqual(created_batch.created_by, self.admin)
        self.assertEqual(created_batch.updated_by, self.admin)
        self.assertEqual(created_batch.status, Batch.Status.DRAFT)

        update_response = self.client.post(
            reverse("batch:batch_edit", kwargs={"pk": created_batch.pk}),
            data={
                "name": "Batch 005 Updated",
                "project": self.project.pk,
                "process": self.process.pk,
                "category": Batch.CategoryChoices.MANUFACTURING,
                "iteration_number": 5,
                "start_date": "",
                "end_date": "",
                "change_justification": "Naming correction",
            },
        )
        self.assertEqual(update_response.status_code, 302)
        created_batch.refresh_from_db()
        self.assertEqual(created_batch.name, "Batch 005 Updated")
        self.assertEqual(created_batch.status, Batch.Status.DRAFT)
        self.assertEqual(created_batch.updated_by, self.admin)

        self.client.force_login(self.admin)
        delete_response = self.client.post(reverse("batch:batch_delete", kwargs={"pk": created_batch.pk}))
        self.assertEqual(delete_response.status_code, 302)
        created_batch.refresh_from_db()
        self.assertFalse(created_batch.is_active)
        self.assertEqual(created_batch.deleted_by, self.admin)

        restore_response = self.client.post(reverse("batch:batch_restore", kwargs={"pk": created_batch.pk}))
        self.assertEqual(restore_response.status_code, 302)
        created_batch.refresh_from_db()
        self.assertTrue(created_batch.is_active)
        self.assertEqual(created_batch.status, Batch.Status.DRAFT)
        self.assertIsNone(created_batch.deleted_by)

    def test_parameter_result_and_analysis_result_list_views(self):
        factory = RequestFactory()

        parameter_request = factory.get(reverse("batch:parameter_result_list"), {"view": "draft"})
        parameter_request.user = self.steward
        parameter_view = ParameterResultListView()
        parameter_view.request = parameter_request
        parameter_view.args = ()
        parameter_view.kwargs = {}
        parameter_queryset = parameter_view.get_queryset()
        parameter_view.object_list = parameter_queryset
        parameter_context = parameter_view.get_context_data(object_list=parameter_queryset)

        self.assertEqual(parameter_queryset.count(), 1)
        self.assertEqual(parameter_context["count_draft"], 1)
        self.assertEqual(parameter_context["count_active"], 0)

        analysis_request = factory.get(reverse("batch:analysis_result_list"), {"view": "draft"})
        analysis_request.user = self.steward
        analysis_view = AnalysisResultListView()
        analysis_view.request = analysis_request
        analysis_view.args = ()
        analysis_view.kwargs = {}
        analysis_queryset = analysis_view.get_queryset()
        analysis_view.object_list = analysis_queryset
        analysis_context = analysis_view.get_context_data(object_list=analysis_queryset)

        self.assertEqual(analysis_queryset.count(), 1)
        self.assertEqual(analysis_context["count_draft"], 1)
        self.assertEqual(analysis_context["count_active"], 0)

    def test_parameter_and_analysis_result_detail_actions_and_workflow(self):
        self.client.force_login(self.steward)

        parameter_detail = self.client.get(reverse("batch:parameter_result_detail", kwargs={"pk": self.parameter_result.pk}))
        parameter_labels = [action["label"] for action in parameter_detail.context["dynamic_actions"]]
        self.assertIn("Edit Record", parameter_labels)
        self.assertIn("Validate", parameter_labels)
        self.assertIn("Reject", parameter_labels)

        analysis_detail = self.client.get(reverse("batch:analysis_result_detail", kwargs={"pk": self.analysis_result.pk}))
        analysis_labels = [action["label"] for action in analysis_detail.context["dynamic_actions"]]
        self.assertIn("Edit Record", analysis_labels)
        self.assertIn("Validate", analysis_labels)
        self.assertIn("Reject", analysis_labels)

        validate_response = self.client.post(
            reverse("batch:parameter_result_validate", kwargs={"pk": self.parameter_result.pk})
        )
        self.assertEqual(validate_response.status_code, 302)
        self.parameter_result.refresh_from_db()
        self.assertEqual(self.parameter_result.status, ParameterResult.Status.VALIDATED)

        reject_response = self.client.post(
            reverse("batch:analysis_result_reject", kwargs={"pk": self.analysis_result.pk}),
            data={"rejection_reason": "Incorrect readout"},
        )
        self.assertEqual(reject_response.status_code, 302)
        self.analysis_result.refresh_from_db()
        self.assertEqual(self.analysis_result.status, AnalysisResult.Status.REJECTED)
        self.assertEqual(self.analysis_result.rejection_reason, "Incorrect readout")

    def test_get_next_iteration_endpoint(self):
        self.client.force_login(self.custodian)

        response = self.client.get(reverse("batch:get_next_iteration"), {"project_id": self.project.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["next_iteration"], 4)

        empty_response = self.client.get(reverse("batch:get_next_iteration"))
        self.assertEqual(empty_response.status_code, 200)
        self.assertEqual(empty_response.json()["next_iteration"], 1)

