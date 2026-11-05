from typing import Dict, Optional
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.http import QueryDict
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from TutorApp.users.tests.factories import UserFactory

from ..factories import ExamFactory, MathMatriculationTasksFactory
from ..models import Book, Exam, MathMatriculationTasks
from ..services import MatriculationTaskService
from ..views import SearchMatriculationTaskView

User = get_user_model()


class ExamCreateViewTest(TestCase):
    def setUp(self):

        self.teacher_user = User.objects.create_superuser(
            "teacher", "a@b.com", "pass1234"
        )
        self.regular_user = User.objects.create_user("user", "u@b.com", "pass1234")
        self.client = Client()
        self.url = reverse("examination_tasks:exam_add")

    def test_get_as_teacher(self):
        self.client.force_login(self.teacher_user)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Add New Exam")

    def test_post_valid_as_admin_creates_and_redirects(self):
        self.client.force_login(self.admin)
        exam = ExamFactory.build()
        data = {
            "year": exam.year,
            "month": exam.month,
            "tasks_link": exam.tasks_link,
            "solutions_link": exam.solutions_link,
            "tasks_count": exam.tasks_count,
            "level_type": exam.level_type,
        }
        r = self.client.post(self.url, data)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Exam.objects.filter(year=exam.year, month=exam.month).exists())

    def test_post_invalid_data_shows_errors(self):
        self.client.force_login(self.admin)
        data = {
            "year": "",
            "month": "",
            "tasks_link": "invalid-url",
            "solutions_link": "invalid-url",
            "tasks_count": -1,
            "level_type": "",
        }
        r = self.client.post(self.url, data)
        self.assertEqual(r.status_code, 200)
        self.assertFormError(r, "form", "year", "This field is required.")
        self.assertFormError(r, "form", "month", "This field is required.")
        self.assertFormError(r, "form", "tasks_link", "Enter a valid URL.")
        self.assertFormError(r, "form", "solutions_link", "Enter a valid URL.")

    def test_access_forbidden_for_non_admin(self):
        self.client.force_login(self.user)
        r_get = self.client.get(self.url)
        r_post = self.client.post(self.url, {})
        self.assertIn(r_get.status_code, (403, 302))
        if r_get.status_code == 302:
            self.assertIn("/login/", r_get.url)
        self.assertIn(r_post.status_code, (403, 302))

    def test_access_forbidden_for_anonymous(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login/", r.url)

    def test_access_forbidden_for_non_teacher(self):
        self.client.force_login(self.regular_user)
        r_get = self.client.get(self.url)
        self.assertEqual(r_get.status_code, 403)

    def test_exam_create_view_context_title(self):
        self.client.force_login(self.teacher_user)
        response = self.client.get(self.url)
        self.assertEqual(response.context["title"], "Add New Exam")


class AddMatriculationTaskViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_superuser(
            username="teacher_add", password="testpass123"
        )
        cls.student = User.objects.create_user(
            username="student_add", password="testpass123"
        )
        cls.exam = ExamFactory()
        cls.url = reverse("examination_tasks:add_matriculation_task")

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)
        self.assertRedirects(response, f"/users/login/?next={self.url}")

    def test_only_teacher_can_access(self):
        self.client.login(username="student", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_teacher_can_view_form(self):
        self.client.login(username="teacher", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add New Matriculation Task")

    def test_teacher_can_submit_valid_task(self):
        self.client.login(username="teacher_add", password="testpass123")
        data = {"exam": self.exam.pk, "task_id": 1, "category": 1}
        response = self.client.post(self.url, data, follow=False)
        self.assertRedirects(
            response, self.url, status_code=302, fetch_redirect_response=False
        )
        self.assertTrue(
            MathMatriculationTasks.objects.filter(exam=self.exam, task_id=1).exists()
        )

    def test_cannot_add_duplicate_task_to_exam(self):
        MathMatriculationTasks.objects.create(
            exam=self.exam, task_id=2, category=2, type=self.exam.level_type
        )
        self.client.login(username="teacher", password="testpass123")
        response = self.client.post(
            self.url, {"exam": self.exam.pk, "task_id": 2, "category": 2}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response,
            "form",
            None,
            ["Math matriculation tasks with this Exam and Task id already exists."],
        )

    def test_add_matriculation_task_view_template_used(self):
        self.client.login(username="teacher_add", password="testpass123")
        response = self.client.get(self.url)
        self.assertTemplateUsed(
            response, "examination_tasks/add_matriculation_task.html"
        )

    def test_add_matriculation_task_view_success_message(self):
        self.client.login(username="teacher_add", password="testpass123")
        data = {"exam": self.exam.pk, "task_id": 3, "category": 1}
        response = self.client.post(self.url, data, follow=True)
        messages = list(response.context["messages"])
        self.assertTrue(any("Task added successfully!" in str(m) for m in messages))


class SearchMatriculationTaskViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.exam1 = ExamFactory(year=2020, month=5, level_type=1)
        self.exam2 = ExamFactory(year=2021, month=6, level_type=2)

        self.task1 = MathMatriculationTasks.objects.create(
            exam=self.exam1, task_id=1, category=1, type=1
        )
        self.task2 = MathMatriculationTasks.objects.create(
            exam=self.exam1, task_id=2, category=2, type=1
        )
        self.task3 = MathMatriculationTasks.objects.create(
            exam=self.exam2, task_id=1, category=1, type=2
        )

        self.url = reverse("examination_tasks:search_tasks")
        self.view = SearchMatriculationTaskView()

    def _create_request(
        self, params: Optional[Dict[str, str]] = None
    ) -> RequestFactory:
        url = self.url
        if params:
            url += f"?{QueryDict('', mutable=True).update(params).urlencode()}"
        request = self.factory.get(url)
        request.user = self.user
        return request

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response.url)

    def test_get_queryset_with_no_filters(self):
        request = self._create_request()
        self.view.request = request

        queryset = self.view.get_queryset()
        self.assertEqual(queryset.count(), 3)
        self.assertIn(self.task1, queryset)
        self.assertIn(self.task2, queryset)
        self.assertIn(self.task3, queryset)

    def test_get_queryset_with_year_filter(self):
        request = self._create_request({"year": "2020"})
        self.view.request = request

        queryset = self.view.get_queryset()
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.task1, queryset)
        self.assertIn(self.task2, queryset)
        self.assertNotIn(self.task3, queryset)

    def test_get_queryset_with_month_filter(self):
        request = self._create_request({"month": "6"})
        self.view.request = request

        queryset = self.view.get_queryset()
        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.task3, queryset)
        self.assertNotIn(self.task1, queryset)
        self.assertNotIn(self.task2, queryset)

    def test_get_queryset_with_level_filter(self):

        request = self._create_request({"level": "2"})
        self.view.request = request

        queryset = self.view.get_queryset()
        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.task3, queryset)
        self.assertNotIn(self.task1, queryset)
        self.assertNotIn(self.task2, queryset)

    def test_get_queryset_with_category_filter(self):
        request = self._create_request({"category": "2"})
        self.view.request = request

        queryset = self.view.get_queryset()
        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.task2, queryset)
        self.assertNotIn(self.task1, queryset)
        self.assertNotIn(self.task3, queryset)

    def test_get_queryset_with_multiple_filters(self):
        request = self._create_request({"year": "2020", "category": "1"})
        self.view.request = request

        queryset = self.view.get_queryset()
        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.task1, queryset)
        self.assertNotIn(self.task2, queryset)
        self.assertNotIn(self.task3, queryset)

    def test_get_queryset_with_invalid_filters(self):
        request = self._create_request(
            {"year": "invalid", "month": "13", "level": "99"}
        )
        self.view.request = request

        queryset = self.view.get_queryset()
        self.assertEqual(queryset.count(), 3)

    def test_get_context_data(self):
        request = self._create_request({"year": "2020"})
        self.view.request = request
        self.view.object_list = self.view.get_queryset()

        context = self.view.get_context_data()

        self.assertEqual(context["title"], "Search Tasks")
        self.assertEqual(context["filter"], {"year": "2020"})
        self.assertIn("task_contents", context)
        self.assertEqual(len(context["task_contents"]), 2)

    def test_pagination(self):
        for i in range(3, 15):
            MathMatriculationTasks.objects.create(
                exam=self.exam1, task_id=i, category=1, type=1
            )

        request = self._create_request()
        self.view.request = request
        self.view.paginate_by = 10

        queryset = self.view.get_queryset()
        self.assertEqual(queryset.count(), 15)

        context = self.view.get_context_data(object_list=queryset[:10])
        self.assertEqual(len(context["object_list"]), 10)
        self.assertTrue(context["is_paginated"])

        context = self.view.get_context_data(object_list=queryset[10:15])
        self.assertEqual(len(context["object_list"]), 5)

    def test_get_int_param_helper(self):
        self.assertEqual(self.view._get_int_param("123"), 123)
        self.assertEqual(self.view._get_int_param(""), None)
        self.assertEqual(self.view._get_int_param(None), None)
        self.assertEqual(self.view._get_int_param("invalid"), None)

    def test_get_bool_param_helper(self):
        self.assertEqual(self.view._get_bool_param("true"), True)
        self.assertEqual(self.view._get_bool_param("false"), False)
        self.assertEqual(self.view._get_bool_param(""), None)
        self.assertEqual(self.view._get_bool_param(None), None)
        self.assertEqual(self.view._get_bool_param("invalid"), None)

    def test_get_queryset_with_invalid_filters_returns_no_results(self):
        response = self.client.get(self.url, {"year": "invalid_year"})
        self.assertEqual(response.status_code, 200)
        queryset = response.context["tasks"]
        self.assertEqual(len(queryset), 0)

    def test_search_view_filter_form_in_context(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.url, {"year": 2020})
        self.assertIn("filter_form", response.context)
        self.assertEqual(int(response.context["filter_form"].data.get("year")), 2020)


class ExamProgressViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password="password123")
        self.exam = ExamFactory(year=2024, month="June", level_type="basic")
        self.task = MathMatriculationTasksFactory(exam=self.exam)

    def test_view_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("examination_tasks:exam_progress"))
        self.assertRedirects(response, "/users/login/?next=/progress/")

    def test_progress_view_base(self):
        response = self.client.get(reverse("examination_tasks:exam_progress"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("years", response.context)

    def test_view_with_year(self):
        response = self.client.get(
            reverse("examination_tasks:exam_progress"),
            {"year": self.exam.year},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("available_months", response.context)
        self.assertIn(self.exam.month, response.context["available_months"])

    def test_view_with_year_and_month(self):
        response = self.client.get(
            reverse("examination_tasks:exam_progress"),
            {"year": self.exam.year, "month": self.exam.month},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("available_levels", response.context)
        self.assertIn(self.exam.level_type, response.context["available_levels"])

    def test_view_with_year_month_level(self):
        response = self.client.get(
            reverse("examination_tasks:exam_progress"),
            {
                "year": self.exam.year,
                "month": self.exam.month,
                "level": self.exam.level_type,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_exam"], self.exam)
        self.assertIn(self.task, response.context["tasks"])

    def test_exam_progress_view_no_exams(self):
        Exam.objects.all().delete()
        response = self.client.get(reverse("examination_tasks:exam_progress"))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get("selected_exam"))
        self.assertEqual(list(response.context.get("tasks", [])), [])

    def test_exam_progress_template_used(self):
        response = self.client.get(reverse("examination_tasks:exam_progress"))
        self.assertTemplateUsed(response, "exam_progress.html")


class TaskViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.exam = ExamFactory(year=2022, month="May", level_type=1)
        self.task = MathMatriculationTasksFactory(exam=self.exam, task_id=1)

    def test_task_view_valid_data(self):
        url = reverse(
            "examination_tasks:task_view",
            kwargs={
                "year": self.exam.year,
                "month": self.exam.month,
                "level": "B",
                "task_id": self.task.task_id,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.exam.tasks_link)

    def test_task_view_exam_not_found(self):
        url = reverse(
            "examination_tasks:task_view",
            kwargs={"year": 1900, "month": "January", "level": "B", "task_id": 1},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @patch("services.pymupdf.open", side_effect=FileNotFoundError)
    def test_get_single_task_text_file_not_found(mock_open):
        result = MatriculationTaskService.get_single_task_text("notfound.pdf", [1])
        assert result is None

    @patch("services.pymupdf.open")
    def test_get_single_task_text_invalid_page_number(mock_open):
        mock_doc = Mock()
        mock_doc.page_count = 1
        mock_open.return_value.__enter__.return_value = mock_doc

        result = MatriculationTaskService.get_single_task_text("fake.pdf", [99])
        assert result is None


class TaskDisplayViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserFactory(password="pass123")
        self.exam = ExamFactory()
        self.task = MathMatriculationTasksFactory(exam=self.exam)
        self.client.login(username=self.user.username, password="pass123")

    @patch("examination_tasks.views.MatriculationTaskService.toggle_completed")
    def test_post_toggles_task_completion(self, mock_toggle):
        mock_toggle.return_value = True
        url = reverse("examination_tasks:task_detail", args=[self.task.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"completed": True})
        mock_toggle.assert_called_once_with(self.task, self.user)


class TaskPdfStreamViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserFactory(password="pass123")
        self.exam = ExamFactory()
        self.task = MathMatriculationTasksFactory(exam=self.exam, pages="1")
        self.client.login(username=self.user.username, password="pass123")

    @patch("examination_tasks.views.MatriculationTaskService.get_single_task_pdf")
    @patch("examination_tasks.views.MatriculationTaskService._parse_pages_string")
    def test_pdf_stream_success(self, mock_parse, mock_get_pdf):
        mock_parse.return_value = [1]
        mock_get_pdf.return_value = b"%PDF-1.4 test content"
        url = reverse("examination_tasks:task_pdf_stream", args=[self.task.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    @patch(
        "examination_tasks.views.MatriculationTaskService._parse_pages_string",
        return_value=None,
    )
    def test_pdf_stream_no_pages_defined(self, mock_parse):
        url = reverse("examination_tasks:task_pdf_stream", args=[self.task.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_task_pdf_view_valid_exam(self):
        url = reverse(
            "examination_tasks:task_view",
            kwargs={
                "year": self.exam.year,
                "month": self.exam.month,
                "level": "B",
                "task_id": self.task.task_id,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("tasks_link", response.context)
        self.assertEqual(response.context["task_id"], self.task.task_id)

    def test_task_pdf_view_invalid_level(self):
        url = reverse(
            "examination_tasks:task_view",
            kwargs={
                "year": self.exam.year,
                "month": self.exam.month,
                "level": "X",
                "task_id": 1,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_task_pdf_view_exam_not_found(self):
        url = reverse(
            "examination_tasks:task_view",
            kwargs={"year": 1900, "month": "January", "level": "B", "task_id": 1},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_exam_list_view_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response.url)

    @patch(
        "examination_tasks.views.MatriculationTaskService.get_user_completion_map_for_exams"
    )
    def test_exam_list_view_context_includes_user_completion(self, mock_completion_map):
        mock_completion_map.return_value = {self.exam1.pk: 5, self.exam2.pk: 0}
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("exams", response.context)
        exams = response.context["exams"]
        self.assertTrue(hasattr(exams[0], "user_completion"))
        completions = [exam.user_completion for exam in exams]
        self.assertIn(5, completions)
        self.assertIn(0, completions)

    def test_pdf_stream_no_pdf_path(self):
        self.task.exam.tasks_link = None
        self.task.exam.save()
        url = reverse("examination_tasks:task_pdf_stream", args=[self.task.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertIn("No defined path", response.content.decode())

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response.url)

    def test_lists_tasks_for_exam(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("tasks", response.context)
        tasks = response.context["tasks"]
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].exam, self.exam)

    def test_context_includes_exam(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["exam"], self.exam)

    def test_context_includes_task_completion_map(self):
        self.task1.completed_by.add(self.user)
        response = self.client.get(self.url)
        tasks = response.context["tasks"]
        completion_statuses = {
            task.task_id: task.is_completed_by_user for task in tasks
        }
        self.assertTrue(completion_statuses[1])
        self.assertFalse(completion_statuses[2])

    def test_pagination_first_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["exams"]), 10)

    @patch(
        "examination_tasks.views.MatriculationTaskService._parse_pages_string",
        return_value=[1],
    )
    @patch(
        "examination_tasks.views.MatriculationTaskService.get_single_task_pdf",
        return_value=None,
    )
    def test_pdf_stream_generation_failure(self, mock_get_pdf, mock_parse):
        url = reverse("examination_tasks:task_pdf_stream", args=[self.task.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertIn("could not be generated", response.content.decode())

    @patch(
        "examination_tasks.views.MatriculationTaskService._parse_pages_string",
        side_effect=Exception("Unexpected error"),
    )
    def test_pdf_stream_internal_server_error(self, mock_parse):
        url = reverse("examination_tasks:task_pdf_stream", args=[self.task.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 500)
        self.assertIn("internal server error", response.content.decode().lower())

    def test_teacher_can_add_book(self):
        self.client.login(username="teacher", password="pass123")
        data = {
            "title": "Test Book",
            "author": "Author Name",
            "publication_year": 2024,
            "school_level": "High School",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Book.objects.filter(title="Test Book").exists())
