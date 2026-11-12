"""Tests for examination_tasks.signals"""

from django.core.files.base import ContentFile
from django.db import models
from django.test import TestCase, override_settings
from examination_tasks.choices import LevelTypeChoices
from examination_tasks.tests.factories import ExamFactory
from factory.django import DjangoModelFactory

IN_MEMORY_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


class FileStorageAssertionMixin:
    """Provide assertions for checking files in the storage."""

    def get_file_names(
        self,
        instance: models.Model,
        field_names: tuple[str, ...],
    ) -> dict[str, str]:
        """
        Collect names of the files stored in the given file fields.

        Args:
             instance: Model instance to read the file fields from.
             field_names: Name of the file fields to collect.

        Returns:
            Mapping of each file field name to the name of its file in the storage.
        """
        return {
            field_name: getattr(instance, field_name).name for field_name in field_names
        }

    def assert_files_exist(
        self,
        instance: models.Model,
        file_names: dict[str, str],
        should_exist: bool,
        stage: str,
    ) -> None:
        """Assert whether the given files exist in the storage.

        Each file is checked in a separate subtest, so a failure
        shows which field and stage it concerns.

        Args:
            instance: Model instance to read the file storages from.
            file_names: Mapping of each file field name to the name of its file.
            should_exist: True if the files are expected to exist, False otherwise.
            stage: Label of the test stage shown in the subtest report.
        """
        for field_name, file_name in file_names.items():
            with self.subTest(field_name=field_name, stage=stage):
                storage = getattr(instance, field_name).storage
                self.assertEqual(storage.exists(file_name), should_exist)


class FileSignalTestsMixin(FileStorageAssertionMixin):
    """Provides file-based signal tests common to all models."""

    factory = type[DjangoModelFactory]
    FILE_FIELDS = tuple[str, ...]


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class ExamFileSignalTests(FileSignalTestsMixin, TestCase):
    """Tests for cleaning up exam files in the storage."""

    factory = ExamFactory
    FILE_FIELDS = ("tasks_file", "solutions_file")

    def test_files_are_removed_after_delete(self) -> None:
        """Deleting an exam removes its files from the storage."""
        exam = ExamFactory()
        file_names = self.get_file_names(exam, self.FILE_FIELDS)

        self.assert_files_exist(
            exam, file_names, should_exist=True, stage="before delete"
        )

        with self.captureOnCommitCallbacks(execute=True):
            exam.delete()

        self.assert_files_exist(
            exam, file_names, should_exist=False, stage="after delete"
        )

    def test_old_file_is_removed_after_replace(self) -> None:
        """Replacing a file removes the old one and keeps the other files intact."""
        for replaced_field in self.FILE_FIELDS:
            with self.subTest(replaced_field=replaced_field):
                exam = ExamFactory()
                file_names = self.get_file_names(exam, self.FILE_FIELDS)

                self.assert_files_exist(
                    exam, file_names, should_exist=True, stage="before replace"
                )

                new_file = ContentFile(b"new content", name=f"new_{replaced_field}.pdf")

                with self.captureOnCommitCallbacks(execute=True):
                    setattr(exam, replaced_field, new_file)
                    exam.save()

                storage = getattr(exam, replaced_field).storage
                old_name = file_names[replaced_field]
                self.assertFalse(storage.exists(old_name))

                new_name = getattr(exam, replaced_field).name
                self.assertTrue(storage.exists(new_name))

                untouched_file_names = {
                    field_name: file_name
                    for field_name, file_name in file_names.items()
                    if field_name != replaced_field
                }

                self.assert_files_exist(
                    exam, untouched_file_names, should_exist=True, stage="after replace"
                )

    def test_files_are_kept_when_other_field_changes(self) -> None:
        """Changing another field keeps files in the storage."""
        exam = ExamFactory()
        file_names = self.get_file_names(exam, self.FILE_FIELDS)

        self.assert_files_exist(
            exam, file_names, should_exist=True, stage="before save"
        )

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            exam.level_type = LevelTypeChoices.EXTENDED
            exam.save()

        self.assertEqual(len(callbacks), 0)

        self.assert_files_exist(exam, file_names, should_exist=True, stage="after save")
