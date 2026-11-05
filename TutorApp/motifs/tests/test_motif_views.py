from django.test import Client, TestCase
from examination_tasks.tests.factories import SectionFactory

from TutorApp.users.tests.factories import TeacherFactory, UserFactory

from ..models import Motif
from .factories import MotifFactory


class AddMotifViewTest(TestCase):

    def setUp(self):

        self.client = Client()

    def test_get_add_motif_page(self):
        """Test GET request to add motif page"""
        response = self.client.get("/motifs/add/")

        self.assertEqual(response.status_code, 403)

    def test_can_teacher_access_page(self):
        """Test case that checks if teacher can access the page"""

        teacher = TeacherFactory()

        self.client.login(username=teacher.username, password="testpass123")

        response = self.client.get("/motifs/add/")

        self.assertEqual(response.status_code, 200)

    def test_can_teacher_add_motif(self):
        """Test case that checks if teacher can add motif"""
        teacher = TeacherFactory()
        self.client.login(username=teacher.username, password="testpass123")

        section = SectionFactory()

        data = {
            "subject": 1,
            "section": section.pk,
            "content": "How to solve equation",
            "answer": "Step by step",
            "level_type": 1,
            "is_mandatory": True,
            "is_in_matriculation_sheets": True,
        }

        response = self.client.post("/motifs/add/", data=data)

        self.assertEqual(response.status_code, 302)

    def test_is_motif_saved_to_database(self):
        """Test case that checks if motif is saved to database"""

        teacher = TeacherFactory()
        self.client.login(username=teacher.username, password="testpass123")

        section = SectionFactory()
        number_of_motifs_before = Motif.objects.count()

        data = {
            "subject": 1,
            "section": section.pk,
            "content": "How to solve equation",
            "answer": "Step by step",
            "level_type": 1,
            "is_mandatory": True,
            "is_in_matriculation_sheets": True,
        }

        self.client.post("/motifs/add/", data=data)

        number_of_motifs_after = Motif.objects.count()

        self.assertEqual(number_of_motifs_after, number_of_motifs_before + 1)

    def test_student_cannot_add_motif(self):
        """Test case that checks if student can add motif"""

        student = UserFactory()

        section = SectionFactory()

        data = {
            "subject": 1,
            "section": section.pk,
            "content": "How to solve equation",
            "answer": "Step by step",
            "level_type": 1,
            "is_mandatory": True,
            "is_in_matriculation_sheets": True,
        }

        self.client.login(username=student.username, password="testpass123")

        response = self.client.post("/motifs/add/", data=data)

        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_cannot_access_add_motif_page(self):
        """Test case that checks if anonymous user cannot access add motif"""

        response = self.client.get("/motifs/add/")

        self.assertEqual(response.status_code, 302)

    def test_saved_motif_has_correct_data(self):
        """Test case that checks if saved motif has correct data"""

        teacher = TeacherFactory()
        section = SectionFactory()

        self.client.login(username=teacher.username, password="testpass123")

        data = {
            "subject": 1,
            "section": section.pk,
            "content": "How to solve equation",
            "answer": "Step by step",
            "level_type": 1,
            "is_mandatory": True,
            "is_in_matriculation_sheets": True,
        }

        self.client.post("/motifs/add/", data=data)

        last_motif = Motif.objects.last()

        self.assertEqual(last_motif.subject, data["subject"])
        self.assertEqual(last_motif.section.pk, data["section"])
        self.assertEqual(last_motif.content, data["content"])
        self.assertEqual(last_motif.answer, data["answer"])
        self.assertEqual(last_motif.level_type, data["level_type"])
        self.assertEqual(last_motif.is_mandatory, data["is_mandatory"])
        self.assertEqual(
            last_motif.is_in_matriculation_sheets,
            data["is_in_matriculation_sheets"],
        )

    def test_form_without_content(self):
        """Test case that checks if form without content is correct"""

        teacher = TeacherFactory()
        section = SectionFactory()

        self.client.login(username=teacher.username, password="testpass123")

        count_before = Motif.objects.count()

        data = {
            "subject": 1,
            "section": section.pk,
            "content": "",
            "answer": "Step by step",
            "level_type": 1,
            "is_mandatory": True,
            "is_in_matriculation_sheets": True,
        }

        response = self.client.post("/motifs/add/", data=data)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(Motif.objects.count(), count_before)

    def test_teacher_can_delete_motif(self):
        """Test that teacher can delete a motif"""

        teacher = TeacherFactory()
        motif = MotifFactory()

        count_before = Motif.objects.count()

        self.client.login(username=teacher.username, password="testpass123")
        response = self.client.post(f"/motifs/{motif.pk}/delete/")

        self.assertEqual(response.status_code, 302)

        self.assertEqual(Motif.objects.count(), count_before - 1)

        self.assertFalse(Motif.objects.filter(pk=motif.pk).exists())

    def test_student_cannot_delete_motif(self):
        """Test that student gets 403 when trying to delete motif"""

        student = UserFactory()
        motif = MotifFactory()

        count_before = Motif.objects.count()

        self.client.login(username=student.username, password="testpass123")
        response = self.client.post(f"/motifs/{motif.pk}/delete/")

        self.assertEqual(response.status_code, 403)

        self.assertEqual(Motif.objects.count(), count_before)
        self.assertTrue(Motif.objects.filter(pk=motif.pk).exists())

    def test_anonymous_cannot_see_list(self):
        """Test case that checks if anonymous user cannot see list"""

        response = self.client.get("/motifs/")

        self.assertEqual(response.status_code, 302)

    def test_logged_user_can_see_motif_list(self):
        """Test case that checks if logged user can see motif list"""

        student = UserFactory()

        self.client.login(username=student.username, password="testpass123")

        response = self.client.get("/motifs/")

        self.assertEqual(response.status_code, 200)

    def test_filtering_by_subject_works(self):
        """Test case that filters motifs by subject"""

        user = UserFactory()

        self.client.login(username=user.username, password="testpass123")

        motif_math = MotifFactory(subject=1)
        motif_physics = MotifFactory(subject=2)

        response = self.client.get("/motifs/?subject=1")
        motifs_in_response = response.context["object_list"]

        self.assertEqual(len(motifs_in_response), 1)

        self.assertIn(motif_math, motifs_in_response)
        self.assertNotIn(motif_physics, motifs_in_response)

    def test_pagination_works(self):
        """Test case that checks if pagination works"""
        MotifFactory.create_batch(15)

        user = UserFactory()

        self.client.login(username=user.username, password="testpass123")

        response = self.client.get("/motifs/")

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context["object_list"]), 10)

    def test_form_validates_url_field(self):
        """Test that explanation_link must be valid URL"""

        teacher = TeacherFactory()
        section = SectionFactory()
        self.client.login(username=teacher.username, password="testpass123")

        count_before = Motif.objects.count()

        data = {
            "subject": 1,
            "section": section.pk,
            "content": "How to solve equation",
            "answer": "Step by step",
            "level_type": 1,
            "is_mandatory": True,
            "is_in_matriculation_sheets": True,
            "explanation_link": "not-a-valid-url",
        }

        response = self.client.post("/motifs/add/", data=data)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(Motif.objects.count(), count_before)

    def test_deleting_nonexistent_motif(self):
        """Test that checks if teacher can delete a non-existent motif"""
        teacher = TeacherFactory()

        self.client.login(username=teacher.username, password="testpass123")

        response = self.client.post("/motifs/9999/delete/")

        self.assertEqual(response.status_code, 404)

    def test_accessing_delete_page_shows_confirmation(self):
        """Test that GET on delete URL shows confirmation page"""
        teacher = TeacherFactory()
        motif = MotifFactory()

        self.client.login(username=teacher.username, password="testpass123")

        response = self.client.get(f"/motifs/{motif.pk}/delete/")

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, "motifs/motif_confirm_delete.html")

        self.assertEqual(Motif.objects.count(), 1)

    def test_filter_empty_motif_list(self):
        """Test that checks if empty motif list works"""

        user = UserFactory()

        self.client.login(username=user.username, password="testpass123")

        response = self.client.get("/motifs/?subject=2")

        motifs_in_response = response.context["object_list"]

        self.assertEqual(len(motifs_in_response), 0)

        self.assertEqual(Motif.objects.count(), 1)
