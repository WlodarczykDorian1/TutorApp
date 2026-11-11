"""Tests for examination_tasks.signals"""

from django.test import TestCase, override_settings
from examination_tasks.tests.factories import ExamFactory

IN_MEMORY_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class ExamDeleteSignalTests(TestCase):
    """Tests for removing attachment files when exams are deleted."""

    FILE_FIELDS = ("tasks_file", "solutions_file")

    def test_files_are_removed_after_delete(self) -> None:
        """Deleting an exam removes its files from the storage."""
        exam = ExamFactory()
        file_names = {
            field_name: getattr(exam, field_name).name
            for field_name in self.FILE_FIELDS
        }

        for field_name, file_name in file_names.items():
            with self.subTest(field_name=field_name, stage="before delete"):
                storage = getattr(exam, field_name).storage
                self.assertTrue(storage.exists(file_name))

        with self.captureOnCommitCallbacks(execute=True):
            exam.delete()

        for field_name, file_name in file_names.items():
            with self.subTest(field_name=field_name, stage="after delete"):
                storage = getattr(exam, field_name).storage
                self.assertFalse(storage.exists(file_name))
