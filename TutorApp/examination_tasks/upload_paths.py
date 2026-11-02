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
            Path such as "Exams/Matriculation/Mathematics/Extended/2024/05/Matriculation_formula_2023/Tasks.pdf"
            or "Exams/Eighth_grade/Mathematics/2024/05/E8_2018/Solutions.pdf"
        """
        parts = [
            "Exams",
            ExamTypeChoices(instance.exam_type).name.capitalize(),
            SubjectChoices(instance.subject).name.capitalize(),
        ]

        if instance.level_type is not None:
            parts.append(LevelTypeChoices(instance.level_type).name.capitalize())

        parts.append(str(instance.year))
        parts.append(f"{instance.month:02d}")
        parts.append(FormulaChoices(instance.formula).name.capitalize())
        category = self.category + ".pdf"
        parts.append(category)
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


def get_exam_segments(exam: "Exam") -> list[str]:
    """
    Gets all segments needed for the exam upload in the following order:
        - exam_type
        - subject
        - level_type
        - year
        - month
        - formula

    Level_type is optional because e8 has level_type == None.

    Args:
        exam: Exam whose fields determine the folder structure.

    Returns:
        List of segments needed for the exam upload.
        Examples:
            [Matriculation, Mathematics, Extended, 2024, 05, Matriculation_formula_2023]
            [Eighth_grade, Mathematics, 2024, 05, E8_2018]
    """
    segments = [
        ExamTypeChoices(exam.exam_type).name.capitalize(),
        SubjectChoices(exam.subject).name.capitalize(),
    ]

    if exam.level_type is not None:
        segments.append(LevelTypeChoices(exam.level_type).name.capitalize())

    segments += [
        str(exam.year),
        f"{exam.month:02d}",
        FormulaChoices(exam.formula).name.capitalize(),
    ]

    return segments
