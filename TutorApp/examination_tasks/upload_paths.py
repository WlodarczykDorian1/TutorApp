from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from courses.choices import SubjectChoices
from django.utils.deconstruct import deconstructible
from examination_tasks.choices import ExamTypeChoices, LevelTypeChoices

if TYPE_CHECKING:
    from examination_tasks.models import Exam


@deconstructible
class ExamUploadPath:
    """
    Callable building storage paths for exam files.

    One class serves several FileFields, they differ only by "category".

    Attributes:
        category: Subdirectory distinguishing file types, e.g. "Tasks", "Solutions".
    """

    def __init__(self, category: str) -> None:
        """
        Initialize the path builder.

        Args:
            category: Subdirectory name for this file type.
        """
        self.category = category

    def __call__(self, instance: "Exam", filename: str) -> str:
        """
        Build the relative storage path.

        Args:
            instance: Exam whose fields determine the folder structure.
            filename: Original uploaded file name (ignored).

        Returns:
            Path such as "Exams/Matriculation/Tasks/Mathematics/Extended/2026/May/2023_Formula.pdf"
            or "Exams/E8/Solutions/Mathematics/2026/May/E8_2018_Formula.pdf"
        """
        if instance.level_type in LevelTypeChoices:
            return str(
                PurePosixPath("Exams")
                / f"{ExamTypeChoices(instance.exam_type).name.capitalize()}"
                / f"{self.category}"
                / f"{SubjectChoices(instance.subject).name.capitalize()}"
                / f"{LevelTypeChoices(instance.level_type).name.capitalize()}"
                / f"{instance.get_month_display()}"
                / f"{instance.get_formula_display()}.pdf"
            )

        return str(
            PurePosixPath("Exams")
            / f"{instance.get_exam_type_display()}"
            / f"{self.category}"
            / f"{instance.get_subject_display()}"
            / f"{instance.get_level_type_display()}"
            / f"{instance.get_year_display()}"
            / f"{instance.get_month_display()}"
            / f"{instance.get_formula_display()}.pdf"
        )

    def __eq__(self, other: object) -> bool:
        """
        Compare builders by configuration.

        Args:
            other: Object to compare.

        Returns:
            True if other is an ExamUploadPath with the same category.
        """

        return isinstance(other, ExamUploadPath) and self.category == other.category
