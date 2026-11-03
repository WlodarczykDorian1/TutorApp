from django.apps import AppConfig


class ExaminationTasksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "examination_tasks"

    def ready(self) -> None:
        """
        Register signal receivers.
        """
        from examination_tasks import signals  # noqa: F401
