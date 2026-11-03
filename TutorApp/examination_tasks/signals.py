from functools import partial

from django.db import transaction
from django.db.models.fields.files import FieldFile


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
