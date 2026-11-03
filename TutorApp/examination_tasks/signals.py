from functools import partial
from typing import Any

from django.db import transaction
from django.db.models.fields.files import FieldFile
from django.db.models.signals import post_delete
from django.dispatch import receiver
from examination_tasks.models import ExamSubtask


def register_file_deletion(field_file: FieldFile) -> None:
    """
    Register a file deletion after the transaction commits.

    Does nothing when no file has been assigned to the field.

    Args:
        field_file: File from the model field that is to be deleted.
    """
    if not field_file.name:
        return

    storage = field_file.storage
    name = field_file.name

    transaction.on_commit(
        partial(storage.delete, name),
    )


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
    register_file_deletion(instance.instruction_screen)
    register_file_deletion(instance.solution_screen)
