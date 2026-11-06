"""Tests for examination_tasks.upload_paths."""

from courses.choices import SubjectChoices
from django.test import SimpleTestCase
from examination_tasks.choices import (
    ExamTypeChoices,
    FormulaChoices,
    LevelTypeChoices,
    MonthChoices,
)
from examination_tasks.models import Exam
from examination_tasks.tests.factories import ExamFactory
from examination_tasks.upload_paths import (
    ExamSubtaskScreensUploadPath,
    ExamUploadPath,
    get_exam_segments,
)


class GetExamSegmentsTests(SimpleTestCase):
    """
    Tests for get_exam_segments.
    """

    def test_returns_segments_for_basic_matriculation(self) -> None:
        """Return full segment list for a basic matriculation exam."""
        exam = ExamFactory.build(
            exam_type=ExamTypeChoices.MATRICULATION,
            subject=SubjectChoices.MATHEMATICS,
            level_type=LevelTypeChoices.BASIC,
            year=2025,
            month=MonthChoices.MAY,
            formula=FormulaChoices.MATRICULATION_FORMULA_2023,
        )

        expected = [
            "Matriculation",
            "Mathematics",
            "Basic",
            "2025",
            "05",
            "Matriculation_formula_2023",
        ]

        segments = get_exam_segments(exam)
        self.assertListEqual(segments, expected)

    def test_returns_segments_for_extended_matriculation(self) -> None:
        """Return full segment list for an extended matriculation exam."""
        exam = ExamFactory.build(
            exam_type=ExamTypeChoices.MATRICULATION,
            subject=SubjectChoices.MATHEMATICS,
            level_type=LevelTypeChoices.EXTENDED,
            year=2025,
            month=MonthChoices.MAY,
            formula=FormulaChoices.MATRICULATION_FORMULA_2023,
        )

        expected = [
            "Matriculation",
            "Mathematics",
            "Extended",
            "2025",
            "05",
            "Matriculation_formula_2023",
        ]

        segments = get_exam_segments(exam)
        self.assertListEqual(segments, expected)

    def test_returns_segments_for_eighth_grade_exam(self) -> None:
        """Return full segment list for an eighth grade exam."""
        exam = ExamFactory.build(
            exam_type=ExamTypeChoices.EIGHTH_GRADE,
            subject=SubjectChoices.MATHEMATICS,
            level_type=None,
            year=2025,
            month=MonthChoices.MAY,
            formula=FormulaChoices.E8_2018,
        )

        expected = ["Eighth_grade", "Mathematics", "2025", "05", "E8_2018"]

        segments = get_exam_segments(exam)
        self.assertListEqual(segments, expected)

    def test_formats_month_as_two_digits(self) -> None:
        """Return months format for 1-digit month and 2-digit month.
        For example 9 -> 09. and 10 -> 10."""
        cases = [
            (MonthChoices.SEPTEMBER, "09"),
            (MonthChoices.OCTOBER, "10"),
        ]

        for month, expected_month in cases:
            with self.subTest(month=month):
                exam = ExamFactory.build(
                    exam_type=ExamTypeChoices.MATRICULATION,
                    subject=SubjectChoices.MATHEMATICS,
                    level_type=LevelTypeChoices.BASIC,
                    year=2025,
                    month=month,
                    formula=FormulaChoices.MATRICULATION_FORMULA_2023,
                )
                segments = get_exam_segments(exam)
                expected = [
                    "Matriculation",
                    "Mathematics",
                    "Basic",
                    "2025",
                    expected_month,
                    "Matriculation_formula_2023",
                ]
                self.assertListEqual(segments, expected)


class ExamUploadPathTests(SimpleTestCase):
    """Tests for ExamUploadPath."""

    def test_builds_path_from_exam_segments_and_category(self) -> None:
        """
        Return full path for an exam file from segments and category.
        """
        exam = ExamFactory.build(
            exam_type=ExamTypeChoices.MATRICULATION,
            subject=SubjectChoices.MATHEMATICS,
            level_type=LevelTypeChoices.BASIC,
            year=2024,
            month=MonthChoices.MAY,
            formula=FormulaChoices.MATRICULATION_FORMULA_2023,
        )

        expected = "Exams/Matriculation/Mathematics/Basic/2024/05/Matriculation_formula_2023/Exercises.pdf"
        path_builder = ExamUploadPath("Exercises")
        result = path_builder(exam, "zadanie.txt")
        self.assertEqual(result, expected)

    def test_ignores_filenames(self) -> None:
        """
        Return the same path for an exam file from two different filenames.
        """
        exam = ExamFactory.build()
        path_builder = ExamUploadPath("Tasks")
        result_txt = path_builder(exam, "zadanie.txt")
        result_png = path_builder(exam, "ćwiczenie.png")
        self.assertEqual(result_txt, result_png)

    def test_equals_when_class_and_category_match(self) -> None:
        """
        Treat objects with the same class and category as equal.
        """
        self.assertEqual(ExamUploadPath("Tasks"), ExamUploadPath("Tasks"))

    def test_not_equals_when_categories_differs(self) -> None:
        """
        Treat objects with different category as not equal.
        """
        self.assertNotEqual(ExamUploadPath("Tasks"), ExamUploadPath("Solutions"))

    def test_not_equals_when_class_differs(self) -> None:
        """
        Treat objects with different classes as not equal.
        """
        self.assertNotEqual(
            ExamUploadPath("Tasks"), ExamSubtaskScreensUploadPath("Tasks")
        )

    def test_deconstructs_import_path(self) -> None:
        """
        Deconstruct to the import path stored in migration files.

        Existing migrations reference ExamUploadPath by this exact path.
        Moving or renaming the class would break loading those migrations.
        """
        path_builder = ExamUploadPath("Tasks")
        path, _, _ = path_builder.deconstruct()
        expected = "examination_tasks.upload_paths.ExamUploadPath"
        self.assertEqual(path, expected)

    def test_reconstructs_equal_object_from_tuple(self) -> None:
        """
        Reconstruct an equal object deconstructed from tuple.

        Django migration files that record the states of objects are in text format.
        Deconstruct() must return tuple which enables to reconstruct the original object.
        """
        original = ExamUploadPath("Tasks")
        _, args, kwargs = original.deconstruct()
        rebuilt = ExamUploadPath(*args, **kwargs)
        self.assertEqual(original, rebuilt)

    def test_exam_file_fields_use_upload_path_with_category(self) -> None:
        """
        Configure each exam file field with an upload path for its category.

        Passing the class instead of an instance to upload_to fails
        only when a file is saved, so it is checked here.
        """
        cases = [
            ("tasks_file", ExamUploadPath("Tasks")),
            ("solutions_file", ExamUploadPath("Solutions")),
        ]

        for field_name, expected in cases:
            with self.subTest(field=field_name):
                upload_to = Exam._meta.get_field(field_name).upload_to
                self.assertEqual(upload_to, expected)
