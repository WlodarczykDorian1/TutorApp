import shutil
import tempfile

from django.test import TestCase, override_settings


class TempMediaRootTestCase(TestCase):
    """
    Create temporary folder for test files.

    Use when testing models that have an Image/FileField.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Create a temporary MEDIA_ROOT and enable it for the whole test class.

        The override must be enabled before super().setUpClass(), because
        super().setUpClass() runs setUpTestData(), where factories may already
        create objects with files. Enabling it later would save those files
        to the real MEDIA_ROOT.
        """
        cls._temp_media_root = tempfile.mkdtemp()
        cls._temp_media_override = override_settings(MEDIA_ROOT=cls._temp_media_root)
        cls._temp_media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Restore the original MEDIA_ROOT and remove the temporary folder.
        """
        super().tearDownClass()
        cls._temp_media_override.disable()
        shutil.rmtree(cls._temp_media_root, ignore_errors=True)
