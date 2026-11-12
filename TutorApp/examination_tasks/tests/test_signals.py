"""Tests for examination_tasks.signals"""

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from examination_tasks.choices import LevelTypeChoices
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

    def test_old_file_is_removed_after_replace(self) -> None:
        """Replacing a file removes the old one and keeps the other files intact."""
        for replaced_field in self.FILE_FIELDS:
            with self.subTest(replaced_field=replaced_field):
                exam = ExamFactory()
                file_names = {
                    field_name: getattr(exam, field_name).name
                    for field_name in self.FILE_FIELDS
                }

                for field_name, file_name in file_names.items():
                    with self.subTest(field_name=field_name, stage="before save"):
                        storage = getattr(exam, field_name).storage
                        self.assertTrue(storage.exists(file_name))

                new_file = ContentFile(b"new content", name=f"new_{replaced_field}.pdf")

                with self.captureOnCommitCallbacks(execute=True):
                    setattr(exam, replaced_field, new_file)
                    exam.save()

                storage = getattr(exam, replaced_field).storage
                old_name = file_names[replaced_field]
                self.assertFalse(storage.exists(old_name))

                new_name = getattr(exam, replaced_field).name
                self.assertTrue(storage.exists(new_name))

                for field_name, file_name in file_names.items():
                    if field_name == replaced_field:
                        continue
                    with self.subTest(field_name=field_name, stage="after save"):
                        storage = getattr(exam, field_name).storage
                        self.assertTrue(storage.exists(file_name))

    def test_files_are_kept_when_other_field_changes(self) -> None:
        """Changing another field keeps files in the storage."""
        exam = ExamFactory()
        file_names = {
            field_name: getattr(exam, field_name).name
            for field_name in self.FILE_FIELDS
        }

        for field_name, file_name in file_names.items():
            with self.subTest(field_name=field_name, stage="before save"):
                storage = getattr(exam, field_name).storage
                self.assertTrue(storage.exists(file_name))

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            exam.level_type = LevelTypeChoices.EXTENDED
            exam.save()

        self.assertEqual(len(callbacks), 0)

        for field_name, file_name in file_names.items():
            with self.subTest(field_name=field_name, stage="after save"):
                storage = getattr(exam, field_name).storage
                self.assertTrue(storage.exists(file_name))
