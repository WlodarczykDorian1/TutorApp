from functools import partial
from typing import Any

from django.core.files.storage import Storage
from django.db import models, transaction
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from examination_tasks.models import Exam, ExamSubtask, ExamTask


def register_file_deletion(storage: Storage, name: str) -> None:
    """
    Register a file deletion after the transaction commits.

    Does nothing when the path is empty.

    Args:
        storage: File storage object.
        name: Path of the file to delete, relative to the storage root.
    """
    if not name:
        return

    transaction.on_commit(
        partial(storage.delete, name),
    )


@receiver(post_delete, sender=Exam)
def delete_exam_files(
    sender: type[Exam],
    instance: Exam,
    **kwargs: Any,
) -> None:
    """
    Delete exam files from the storage after the exam is deleted.

    Works for single deletes, queryset deletes and cascades,
    because post_delete is sent for every deleted object.

    Args:
        sender: Model class that sent the signal.
        instance: Exam that has just been deleted.
        **kwargs: Extra signal arguments (unused).
    """
    register_file_deletion(instance.tasks_file.storage, instance.tasks_file.name)
    register_file_deletion(
        instance.solutions_file.storage, instance.solutions_file.name
    )


@receiver(post_delete, sender=ExamTask)
def delete_exam_task_screen(
    sender: type[ExamTask],
    instance: ExamTask,
    **kwargs: Any,
) -> None:
    """
    Delete exam task screen from the storage after the exam task is deleted.

    Works for single deletes, queryset deletes and cascades,
    because post_delete is sent for every deleted object.

    Args:
        sender: Model class that sent the signal.
        instance: Exam task that has just been deleted.
        **kwargs: Extra signal arguments (unused).
    """
    register_file_deletion(instance.intro_screen.storage, instance.intro_screen.name)


@receiver(post_delete, sender=ExamSubtask)
def delete_subtask_screens(
    sender: type[ExamSubtask],
    instance: ExamSubtask,
    **kwargs: Any,
) -> None:
    """
    Delete exam subtask screens from the storage after the subtask is deleted.

    Works for single deletes, queryset deletes and cascades,
    because post_delete is sent for every deleted object.

    Args:
        sender: Model class that sent the signal.
        instance: Subtask that has just been deleted.
        **kwargs: Extra signal arguments (unused).
    """
    register_file_deletion(
        instance.instruction_screen.storage, instance.instruction_screen.name
    )
    register_file_deletion(
        instance.solution_screen.storage, instance.solution_screen.name
    )


def delete_replaced_files(
    sender: type[models.Model],
    instance: models.Model,
    file_field_names: list[str],
    raw: bool,
) -> None:
    """
    Schedule deletion of old files that are being replaced with new ones.

    Args:
        sender: Model class that sent the signal.
        instance: Model instance about to be saved.
        file_field_names: List of file field names from model.
        raw: True when the instance is saved as-is from a fixture (loaddata).
            The database may be inconsistent then, so nothing is done.
    """
    if raw:
        return

    if instance._state.adding:
        return

    old = (
        sender._default_manager.filter(pk=instance.pk).values(*file_field_names).first()
    )

    if old is None:
        return

    for field_name in old:
        new_file = getattr(instance, field_name)
        old_name = old[field_name]

        if old_name != new_file.name:
            register_file_deletion(new_file.storage, old_name)


@receiver(pre_save, sender=ExamSubtask)
def delete_replaced_exam_subtask_screens(
    sender: type[ExamSubtask],
    instance: ExamSubtask,
    raw: bool,
    **kwargs: Any,
) -> None:
    """
    Delete old screens when they are replaced with new ones.

    Args:
        sender: Model class that sent the signal.
        instance: Subtask about to be saved.
        raw: True when the instance is saved as-is from a fixture (loaddata).
            The database may be inconsistent then, so nothing is done.
        **kwargs: Extra signal arguments (unused).
    """
    delete_replaced_files(
        sender, instance, ["instruction_screen", "solution_screen"], raw
    )


@receiver(pre_save, sender=Exam)
def delete_replaced_exam_files(
    sender: type[Exam],
    instance: Exam,
    raw: bool,
    **kwargs: Any,
) -> None:
    """
    Delete old exam and solution file when they are replaced with new ones.

    Args:
        sender: Model class that sent the signal.
        instance: Exam about to be saved.
        raw: True when the instance is saved as-is from a fixture (loaddata).
            The database may be inconsistent then, so nothing is done.
        **kwargs: Extra signal arguments (unused).
    """
    delete_replaced_files(sender, instance, ["tasks_file", "solutions_file"], raw)


@receiver(pre_save, sender=ExamTask)
def delete_replaced_exam_task_screen(
    sender: type[ExamTask],
    instance: ExamTask,
    raw: bool,
    **kwargs: Any,
) -> None:
    """
    Delete old exam task intro screen when it is replaced with new one.

    Args:
        sender: Model class that sent the signal.
        instance: Exam task about to be saved.
        raw: True when the instance is saved as-is from a fixture (loaddata).
            The database may be inconsistent then, so nothing is done.
        **kwargs: Extra signal arguments (unused).
    """
    delete_replaced_files(sender, instance, ["intro_screen"], raw)
