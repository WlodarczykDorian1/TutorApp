"""Tests for examination_tasks.upload_paths."""

from courses.choices import SubjectChoices
from django.test import SimpleTestCase
from examination_tasks.choices import ExamTypeChoices, FormulaChoices, LevelTypeChoices
from examination_tasks.tests.factories import ExamFactory
from examination_tasks.upload_paths import get_exam_segments


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
            month=5,
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
