from functools import partial
from typing import Any

from django.core.files.storage import Storage
from django.db import transaction
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


@receiver(pre_save, sender=ExamSubtask)
def delete_replaced_exam_subtask_screens(
    sender: type[ExamSubtask],
    instance: ExamSubtask,
    **kwargs: Any,
) -> None:
    """
    Delete old screens when they are replaced with new ones.

    Args:
        sender: Model class that sent the signal.
        instance: Subtask about to be saved.
        **kwargs: Extra signal arguments (unused).
    """
    if instance._state.adding:
        return

    old = (
        sender.objects.filter(pk=instance.pk)
        .values("instruction_screen", "solution_screen")
        .first()
    )

    if old is None:
        return

    for field_name in old:
        new_file = getattr(instance, field_name)
        old_name = old[field_name]

        if old_name != new_file.name:
            register_file_deletion(new_file.storage, old_name)
