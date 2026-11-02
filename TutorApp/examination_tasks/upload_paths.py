from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from courses.choices import SubjectChoices
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from examination_tasks.choices import ExamTypeChoices, FormulaChoices, LevelTypeChoices

if TYPE_CHECKING:
    from examination_tasks.models import Exam, ExamSubtask, ExamTask


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
        parts = ["Exams", *get_exam_segments(instance), self.category + ".pdf"]
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


def timestamp_segment() -> str:
    """
    Build a timestamp used to make file names unique between versions.

    Returns:
         UTC timestamp such as "20261102T153000".
    """
    return timezone.now().strftime("%Y%m%dT%H%M%S")


@deconstructible
class ExamTaskIntroScreenUploadPath:
    """
    Callable building storage paths for task intro_screen.
    """

    def __call__(self, instance: "ExamTask", filename: str) -> str:
        """
        Build the relative storage path.

        Args:
            instance: Exam task owning the screen.
            filename: Original uploaded file name (ignored).

        Returns:
            Path such as "ExamScreens/Matriculation/Mathematics/Extended/2026/05/Matriculation_formula_2023/12/Intro_20261102T160000.png"
            or "ExamScreens/Eighth_grade/Mathematics/2026/05/E8_2018/03/Intro_20180602T160000.png"
        """
        parts = [
            "ExamScreens",
            *get_exam_segments(instance.exam),
            f"{instance.number:02d}",
            f"Intro_{timestamp_segment()}.png",
        ]
        return str(PurePosixPath(*parts))

    def __eq__(self, other: object) -> bool:
        """
        Compare builders by configuration.

        Args:
            other: Object to compare.

        Returns:
            True if other is an ExamTaskIntroScreenUploadPath.
        """
        return isinstance(other, ExamTaskIntroScreenUploadPath)


@deconstructible
class ExamSubtaskScreensUploadPath:
    """
    Callable building storage paths for subtask screens.

    Attributes:
        category: Subname distinguishing file types, e.g. "Instruction", "Solution".
    """

    def __init__(self, category: str) -> None:
        """
        Initialize the path builder.

        Args:
            category: Subname for this file type.
        """
        self.category = category

    def __call__(self, instance: "ExamSubtask", filename: str) -> str:
        """
        Build storage paths for subtask screens.

        Args:
            instance: Exam subtask owning the screen.
            filename: Original uploaded file name (ignored).

        Returns:
            Path such as "ExamScreens/Matriculation/Mathematics/Extended/2026/05/Matriculation_formula_2023/12/Instruction_01_20261102T160000.png"
            or "ExamScreens/Eighth_grade/Mathematics/2026/05/E8_2018/03/Solution_20261102T160000.png"
        """
        file_name_parts = [self.category]

        if instance.subnumber is not None:
            file_name_parts.append(f"{instance.subnumber:02d}")

        file_name_parts.append(timestamp_segment())
        file_name = "_".join(file_name_parts) + ".png"

        parts = [
            "ExamScreens",
            *get_exam_segments(instance.exam_task.exam),
            f"{instance.exam_task.number:02d}",
            file_name,
        ]
        return str(PurePosixPath(*parts))

    def __eq__(self, other: object) -> bool:
        """
        Compare builders by configuration.

        Args:
            other: Object to compare.

        Returns:
            True if other is an ExamSubtaskScreensUploadPath with the same category.
        """
        return (
            isinstance(other, ExamSubtaskScreensUploadPath)
            and self.category == other.category
        )
