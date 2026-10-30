from typing import TYPE_CHECKING

from django.utils.deconstruct import deconstructible

if TYPE_CHECKING:
    pass


@deconstructible
class ExamUploadPath:
    """
    Callable building storage paths for exam files.

    One class serves several FileFields, they differ only by "category".

    Attributes:
        category: Subdirectory distinguishing file types, e.g. "tasks", "solutions".
    """

    def __init__(self, category: str) -> None:
        """
        Initialize the path builder.

        Args:
            category: Subdirectory name for this file type.
        """
        self.category = category

    def __eq__(self, other: object) -> bool:
        """
        Compare builders by configuration.

        Args:
            other: Object to compare.

        Returns:
            True if other is an ExamUploadPath with the same category.
        """

        return isinstance(other, ExamUploadPath) and self.category == other.category
