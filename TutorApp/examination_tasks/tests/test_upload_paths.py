"""Tests for examination_tasks.upload_paths."""

from datetime import UTC, datetime
from unittest.mock import patch

from courses.choices import SubjectChoices
from django.test import SimpleTestCase
from examination_tasks.choices import (
    ExamTypeChoices,
    FormulaChoices,
    LevelTypeChoices,
    MonthChoices,
)
from examination_tasks.models import Exam, ExamTask
from examination_tasks.tests.factories import (
    ExamFactory,
    ExamSubtaskFactory,
    ExamTaskFactory,
)
from examination_tasks.upload_paths import (
    ExamSubtaskScreensUploadPath,
    ExamTaskIntroScreenUploadPath,
    ExamUploadPath,
    get_exam_segments,
)


class FrozenTimeTestCase(SimpleTestCase):
    """
    Freeze timezone.now() used by examination_tasks.upload_paths.

    Every test sees FROZEN_NOW as the current time, so paths
    containing a timestamp can be compared with literals.
    Subclasses overriding setUp() must call super().setUp().
    """

    FROZEN_NOW = datetime(2026, 11, 8, 21, 37, 42, tzinfo=UTC)

    def setUp(self) -> None:
        """
        Freeze the current time for every test in subclasses.
        """
        super().setUp()
        patcher = patch(
            "examination_tasks.upload_paths.timezone.now", return_value=self.FROZEN_NOW
        )
        patcher.start()
        self.addCleanup(patcher.stop)


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
            with self.subTest(field_name=field_name):
                upload_to = Exam._meta.get_field(field_name).upload_to
                self.assertEqual(upload_to, expected)


class ExamTaskIntroScreenUploadPathTests(FrozenTimeTestCase):
    """
    Tests for ExamTaskIntroScreenUploadPath.
    """

    def test_builds_path_from_exam_segments_and_date(self) -> None:
        """
        Return a full path for a task intro from segments and date.
        """
        exam = ExamFactory.build(
            exam_type=ExamTypeChoices.MATRICULATION,
            subject=SubjectChoices.MATHEMATICS,
            level_type=LevelTypeChoices.BASIC,
            year=2024,
            month=MonthChoices.MAY,
            formula=FormulaChoices.MATRICULATION_FORMULA_2023,
        )
        exam_task = ExamTaskFactory.build(exam=exam, number=1)
        expected = "ExamScreens/Matriculation/Mathematics/Basic/2024/05/Matriculation_formula_2023/01/Intro_20261108T213742.png"
        path_builder = ExamTaskIntroScreenUploadPath()

        result = path_builder(exam_task, "zadanie.txt")

        self.assertEqual(result, expected)

    def test_ignores_filenames(self) -> None:
        """
        Return the same path for an exam task file from two different filenames.
        """
        exam_task = ExamTaskFactory.build()
        path_builder = ExamTaskIntroScreenUploadPath()

        result_1 = path_builder(exam_task, "zadanie.txt")
        result_2 = path_builder(exam_task, "ćwiczenie.jpg")

        self.assertEqual(result_1, result_2)

    def test_formats_task_number_as_two_digits(self) -> None:
        """
        Return exam task number format for 1-digit number and 2-digit number.
        For example 9 -> 09. and 10 -> 10.
        """
        cases = [
            (9, "09"),
            (10, "10"),
        ]
        exam = ExamFactory.build(
            exam_type=ExamTypeChoices.MATRICULATION,
            subject=SubjectChoices.MATHEMATICS,
            level_type=LevelTypeChoices.BASIC,
            year=2024,
            month=MonthChoices.MAY,
            formula=FormulaChoices.MATRICULATION_FORMULA_2023,
        )
        path_builder = ExamTaskIntroScreenUploadPath()
        for number, expected_number in cases:
            with self.subTest(number=number):
                exam_task = ExamTaskFactory.build(
                    exam=exam,
                    number=number,
                )
                expected = f"ExamScreens/Matriculation/Mathematics/Basic/2024/05/Matriculation_formula_2023/{expected_number}/Intro_20261108T213742.png"
                result = path_builder(exam_task, "zadanie.txt")
                self.assertEqual(result, expected)

    def test_equals_when_class_match(self) -> None:
        """
        Treat objects with the same class as equal.
        """
        self.assertEqual(
            ExamTaskIntroScreenUploadPath(), ExamTaskIntroScreenUploadPath()
        )

    def test_not_equals_when_class_differs(self) -> None:
        """
        Treat objects with different class as not equal.
        """
        self.assertNotEqual(ExamTaskIntroScreenUploadPath(), ExamUploadPath("Tasks"))

    def test_deconstructs_import_path(self) -> None:
        """
        Deconstruct to the import path stored in migration files.

        Existing migrations reference ExamTaskIntroScreenUploadPath by this exact path.
        Moving or renaming the class would break loading those migrations.
        """
        path_builder = ExamTaskIntroScreenUploadPath()
        path, _, _ = path_builder.deconstruct()
        expected_path = "examination_tasks.upload_paths.ExamTaskIntroScreenUploadPath"
        self.assertEqual(path, expected_path)

    def test_exam_task_file_field_uses_upload_path(self) -> None:
        """
        Configure intro screen field with an upload path.

        Passing the class instead of an instance to upload_to fails
        only when a file is saved, so it is checked here.
        """
        expected = ExamTaskIntroScreenUploadPath()
        upload_to = ExamTask._meta.get_field("intro_screen").upload_to
        self.assertEqual(upload_to, expected)


class ExamSubtaskScreensUploadPathTests(FrozenTimeTestCase):
    """
    Tests for ExamSubtaskScreensUploadPath.
    """

    def test_builds_file_path_with_subnumber(self) -> None:
        """
        Return a full path for a subtask from segments, task number, task subnumber and date.
        """
        exam = ExamFactory.build(
            exam_type=ExamTypeChoices.MATRICULATION,
            subject=SubjectChoices.MATHEMATICS,
            level_type=LevelTypeChoices.BASIC,
            year=2024,
            month=MonthChoices.MAY,
            formula=FormulaChoices.MATRICULATION_FORMULA_2023,
        )
        exam_task = ExamTaskFactory.build(
            exam=exam,
            number=1,
        )
        exam_subtask = ExamSubtaskFactory.build(
            exam_task=exam_task,
            subnumber=2,
        )
        expected = "ExamScreens/Matriculation/Mathematics/Basic/2024/05/Matriculation_formula_2023/01/Exercise_02_20261108T213742.png"
        path_builder = ExamSubtaskScreensUploadPath("Exercise")
        result = path_builder(exam_subtask, "zadanie.txt")
        self.assertEqual(result, expected)

    def test_builds_file_path_without_subnumber(self) -> None:
        """
        Return a full path for a subtask from segments, task number but without subnumber.
        """
        exam = ExamFactory.build(
            exam_type=ExamTypeChoices.MATRICULATION,
            subject=SubjectChoices.MATHEMATICS,
            level_type=LevelTypeChoices.BASIC,
            year=2024,
            month=MonthChoices.MAY,
            formula=FormulaChoices.MATRICULATION_FORMULA_2023,
        )
        exam_task = ExamTaskFactory.build(
            exam=exam,
            number=1,
        )
        exam_subtask = ExamSubtaskFactory.build(
            exam_task=exam_task, null_subnumber=True
        )
        expected = "ExamScreens/Matriculation/Mathematics/Basic/2024/05/Matriculation_formula_2023/01/Exercise_20261108T213742.png"
        path_builder = ExamSubtaskScreensUploadPath("Exercise")
        result = path_builder(exam_subtask, "zadanie.txt")
        self.assertEqual(result, expected)

    def test_formats_task_subnumber_as_two_digits(self) -> None:
        """
        Return exam task subnumber format for 1-digit number and 2-digit number.
        For example 9 -> 09. and 10 -> 10.
        """
        cases = [
            (9, "09"),
            (10, "10"),
        ]
        exam = ExamFactory.build(
            exam_type=ExamTypeChoices.MATRICULATION,
            subject=SubjectChoices.MATHEMATICS,
            level_type=LevelTypeChoices.BASIC,
            year=2024,
            month=MonthChoices.MAY,
            formula=FormulaChoices.MATRICULATION_FORMULA_2023,
        )
        exam_task = ExamTaskFactory.build(
            exam=exam,
            number=1,
        )
        path_builder = ExamSubtaskScreensUploadPath("Exercise")
        for subnumber, expected_subnumber in cases:
            with self.subTest(subnumber=subnumber):
                exam_subtask = ExamSubtaskFactory.build(
                    exam_task=exam_task,
                    subnumber=subnumber,
                )
                expected = f"ExamScreens/Matriculation/Mathematics/Basic/2024/05/Matriculation_formula_2023/01/Exercise_{expected_subnumber}_20261108T213742.png"
                result = path_builder(exam_subtask, "zadanie.txt")
                self.assertEqual(result, expected)

    def test_formats_task_number_as_two_digits(self) -> None:
        """
        Return exam task number format for 1-digit number and 2-digit number.
        """
        cases = [
            (9, "09"),
            (10, "10"),
        ]
        exam = ExamFactory.build(
            exam_type=ExamTypeChoices.MATRICULATION,
            subject=SubjectChoices.MATHEMATICS,
            level_type=LevelTypeChoices.BASIC,
            year=2024,
            month=MonthChoices.MAY,
            formula=FormulaChoices.MATRICULATION_FORMULA_2023,
        )
        path_builder = ExamSubtaskScreensUploadPath("Exercise")
        for number, expected_number in cases:
            with self.subTest(number=number):
                exam_task = ExamTaskFactory.build(
                    exam=exam,
                    number=number,
                )
                exam_subtask = ExamSubtaskFactory.build(
                    exam_task=exam_task, subnumber=1
                )
                expected = f"ExamScreens/Matriculation/Mathematics/Basic/2024/05/Matriculation_formula_2023/{expected_number}/Exercise_01_20261108T213742.png"
                result = path_builder(exam_subtask, "zadanie.txt")
                self.assertEqual(result, expected)

    def test_ignores_filenames(self) -> None:
        """
        Return the same path for an exam subtask file from two different filenames.
        """
        exam_subtask = ExamSubtaskFactory.build()
        path_builder = ExamSubtaskScreensUploadPath("Exercise")
        result_1 = path_builder(exam_subtask, "zadanie.txt")
        result_2 = path_builder(exam_subtask, "cwiczenie.gif")
        self.assertEqual(result_1, result_2)

    def test_equals_when_class_and_category_match(self) -> None:
        """
        Treat objects with the same class and category as equal.
        """
        self.assertEqual(
            ExamSubtaskScreensUploadPath("Exercise"),
            ExamSubtaskScreensUploadPath("Exercise"),
        )

    def test_not_equals_when_class_differs(self) -> None:
        """
        Treat objects with different class as not equal.
        """
        self.assertNotEqual(
            ExamSubtaskScreensUploadPath("Exercise"),
            ExamUploadPath("Exercise"),
        )

    def test_not_equals_when_category_differs(self) -> None:
        """
        Treat objects with different category as not equal.
        """
        self.assertNotEqual(
            ExamSubtaskScreensUploadPath("Exercise"),
            ExamSubtaskScreensUploadPath("Answers"),
        )
