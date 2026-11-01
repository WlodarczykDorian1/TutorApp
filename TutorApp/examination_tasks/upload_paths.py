from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from courses.choices import SubjectChoices
from django.utils.deconstruct import deconstructible
from examination_tasks.choices import ExamTypeChoices, FormulaChoices, LevelTypeChoices

if TYPE_CHECKING:
    from examination_tasks.models import Exam


@deconstructible
class ExamUploadPath:
    """
    Callable building storage paths for exam files.

    One class serves several FileFields, they differ only by "category".
    The paths depend on the names of the enum members,
    changing them will alter the path of new files.


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
            Path such as "Exams/Matriculation/Tasks/Math/Extended/2024/05/Matriculation_formula_2023.pdf"
            or "Exams/Eighth_grade/Solutions/Math/2024/05/E8_2018.pdf"
        """
        parts = [
            "Exams",
            ExamTypeChoices(instance.exam_type).name.capitalize(),
            self.category,
            SubjectChoices(instance.subject).name.capitalize(),
        ]

        if instance.level_type is not None:
            parts.append(LevelTypeChoices(instance.level_type).name.capitalize())

        parts.append(str(instance.year))
        parts.append(f"{instance.month:02d}")
        formula = FormulaChoices(instance.formula).name.capitalize() + ".pdf"
        parts.append(formula)
        return str(PurePosixPath(*parts))

    def __eq__(self, other: object) -> bool:
        """
        Compare builders by configuration.

        Args:
            other: Object to compare.

        Returns:
            True if other is an ExamUploadPath with the same category.
        """
        return isinstance(other, ExamUploadPath) and self.category == other.category
