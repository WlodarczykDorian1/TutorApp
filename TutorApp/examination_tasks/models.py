import os

from courses.choices import SubjectChoices
from courses.models import Topic
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from examination_tasks.choices import (
    E8_EXAM_FORMULAS,
    LEVEL_CHOICES,
    MATRICULATION_EXAM_FORMULAS,
    MONTH_CHOICES,
    YEAR_CHOICES,
    ExamTypeChoices,
    FormulaChoices,
)


class Exam(models.Model):
    """
    A single compulsory state examination.

    Each exam belongs to one subject.
    Some fields like level only make sense for matriculation exam
    which is enforced at the database level by constraints defined in Meta.

    Attributes:
        exam_type: Type of exam, a value from ExamTypeChoices.
        subject: Subject of the exam, a value from SubjectChoices.
        formula: Formula of the exam, a value from FormulaChoices
            and it must belong to a specific type of exam.
            E8 also contains EXAM_BEFORE_E8_2002_2019,
            because before E8 there were lower secondary schools.
        year: Year of the exam, a value from YEAR_CHOICES.
        month: Month of the exam, a value from MONTH_CHOICES.
        tasks_file: Pdf file containing exam tasks.
        solutions_file: Pdf file containing exam tasks solutions.
        level_type: Level of the exam (basic or extended,
            only for matriculation exam).
    """

    exam_type = models.IntegerField(
        choices=ExamTypeChoices.choices,
        default=ExamTypeChoices.MATRICULATION,
        verbose_name="Exam type",
    )
    subject = models.IntegerField(
        choices=SubjectChoices.choices,
        verbose_name="Subject",
    )
    formula = models.IntegerField(
        choices=FormulaChoices.choices,
        verbose_name="Formula",
    )
    year = models.IntegerField(choices=YEAR_CHOICES)
    month = models.IntegerField(choices=MONTH_CHOICES)
    tasks_file = models.FileField(upload_to="exam_pdfs/")
    solutions_file = models.FileField(
        upload_to="exam_answers_pdfs/",
    )
    level_type = models.IntegerField(
        choices=LEVEL_CHOICES,
        null=True,
        blank=True,
        help_text="Exam level: basic or extended (Matriculation only)",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "exam_type",
                    "subject",
                    "year",
                    "month",
                    "level_type",
                    "formula",
                ],
                name="exam_unique_type_subject_year_month_level_formula",
                nulls_distinct=False,
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        exam_type=ExamTypeChoices.MATRICULATION,
                        level_type__isnull=False,
                        formula__in=MATRICULATION_EXAM_FORMULAS,
                    )
                    | Q(
                        exam_type=ExamTypeChoices.EIGHTH_GRADE,
                        level_type__isnull=True,
                        formula__in=E8_EXAM_FORMULAS,
                    )
                ),
                name="exam_fields_match_exam_type",
            ),
        ]
        ordering = ["-year", "-month", "-exam_type", "-level_type"]

    def __str__(self) -> str:
        """
        Return a human-readable description of the exam.

        Returns:
            A string such "Mathematics 2023 Matriculation Exam 2024 August - extended"
        """
        month_display = self.get_month_display()
        subject_display = self.get_subject_display()
        formula_display = self.get_formula_display()

        if self.exam_type == ExamTypeChoices.MATRICULATION:
            level_display = self.get_level_type_display()
            level_str = f"– {level_display.lower()}" if level_display else ""
            return (
                f"{subject_display} formula: {formula_display} "
                f"{self.year} {month_display} {level_str}"
            )

        return f"{subject_display} {formula_display} " f"{self.year} {month_display}"


def exam_task_upload_path(instance, filename):
    exam = instance.exam
    return os.path.join(
        "exam_tasks",
        str(exam.get_subject_display()),
        str(exam.exam_type),
        str(exam.year),
        str(exam.month),
        f"zadanie_{instance.number}.pdf",
    )


class ExamTask(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="tasks")
    number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Number",
    )
    task_screen = models.FileField(
        upload_to=exam_task_upload_path,
        null=False,
        blank=False,
        verbose_name="Task PDF",
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        related_name="exam_tasks",
        verbose_name="Topic",
        null=True,
        blank=True,
    )
    task_content = models.TextField(
        blank=True,
        help_text="The extracted content of the task from the PDF file.",
    )
    task_pages = models.CharField(
        max_length=20,
        blank=True,
        help_text="Page number(s) in the PDF, e.g., '5' or '5-6'.",
        verbose_name="Task Pages",
    )
    answer_pages = models.CharField(
        max_length=20,
        blank=True,
        help_text="Page number(s) in the PDF with the solution.",
        verbose_name="Answer Pages",
    )
    completed_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="completed_exam_tasks",
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["exam", "number"],
                name="exam_task_unique_number",
                violation_error_message="Exam task number already exists in this exam.",
            ),
            models.CheckConstraint(
                condition=Q(
                    number__gte=1,
                ),
                name="exam_task_positive_number",
            ),
        ]
        verbose_name = "Exam Task"
        verbose_name_plural = "Exam Tasks"
        ordering = ["exam", "number"]

    def __str__(self) -> str:
        """
        Return a human-readable description of the exam task.

        Returns:
            A string such as "Mathematics 2023 Matriculation Exam 2024 August - extended - Task 1"
        """
        return f"{self.exam} – Task {self.number}"
