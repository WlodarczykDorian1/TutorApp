from core.tests.base import TempMediaRootTestCase
from django.conf import settings
from examination_tasks.tests.factories import ExamFactory


class TempMediaSmokeTests(TempMediaRootTestCase):
    def test_files_go_to_temp_dir(self) -> None:
        exam = ExamFactory()
        self.assertTrue(exam.tasks_file.path.startswith(settings.MEDIA_ROOT))
