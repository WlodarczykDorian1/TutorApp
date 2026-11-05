from core.tests.base import TempMediaRootTestCase
from django.conf import settings
from examination_tasks.choices import ExamTypeChoices
from examination_tasks.models import Exam
from examination_tasks.tests.factories import (
    ExamFactory,
    ExamSubtaskFactory,
    ExamTaskFactory,
)


class TempMediaSmokeTests(TempMediaRootTestCase):
    """Check that files created by factories land in the temporary MEDIA_ROOT."""

    def test_files_go_to_temp_dir(self) -> None:
        exam = ExamFactory()
        self.assertTrue(exam.tasks_file.path.startswith(settings.MEDIA_ROOT))


class ExamTaskFactorySmokeTests(TempMediaRootTestCase):
    """Check how ExamTaskFactory creates related exams."""

    def test_batch_without_exam_creates_separate_exams(self) -> None:
        ExamTaskFactory.create_batch(3)
        self.assertEqual(Exam.objects.count(), 3)

    def test_batch_with_exam_shares_one_exam(self) -> None:
        exam = ExamFactory()
        tasks = ExamTaskFactory.create_batch(3, exam=exam)
        numbers = [task.number for task in tasks]

        self.assertEqual(Exam.objects.count(), 1)
        self.assertEqual(len(numbers), len(set(numbers)))


class ExamSubtaskFactorySmokeTests(TempMediaRootTestCase):
    """Check ExamSubtaskFactory defaults, topics and traits."""

    def test_subtask_has_default_topic(self) -> None:
        subtask = ExamSubtaskFactory()
        self.assertEqual(subtask.topics.count(), 1)

    def test_explicit_empty_topics(self) -> None:
        subtask = ExamSubtaskFactory(topics=[])
        self.assertEqual(subtask.topics.count(), 0)

    def test_traits_combine(self) -> None:
        subtask = ExamSubtaskFactory(e8=True, null_subnumber=True)
        exam = subtask.exam_task.exam

        self.assertEqual(exam.exam_type, ExamTypeChoices.EIGHTH_GRADE)
        self.assertIsNone(subtask.subnumber)
