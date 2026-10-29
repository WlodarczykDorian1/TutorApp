import os

from core import settings
from courses.choices import SubjectChoices
from courses.models import Topic
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _
from examination_tasks.choices import (
    E8_EXAM_FORMULAS,
    LEVEL_CHOICES,
    MATRICULATION_EXAM_FORMULAS,
    MONTH_CHOICES,
    YEAR_CHOICES,
    ExamTypeChoices,
    FormulaChoices,
    FragmentTypeChoices,
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
        verbose_name=_("Exam type"),
    )
    subject = models.IntegerField(
        choices=SubjectChoices.choices,
        verbose_name=_("Subject"),
    )
    formula = models.IntegerField(
        choices=FormulaChoices.choices,
        verbose_name=_("Formula"),
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
        help_text=_("Exam level: basic or extended (Matriculation only)"),
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
                name="exam_valid_level_type_formula",
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
    """
    A single examination task.

    Each exam task has at least one ExamSubtask, even without sub-questions.
    Exam task content without sub-questions can be found in ExamSubtask.
    Pages containing the task and their solutions are calculated
    automatically on the basis of the coordinates of the clips
    from ExamTaskFragment.
    Pages are empty as long as the clips do not exist.

    Attributes:
        exam: An exam that includes a task.
        number: A task number that is unique within the exam.
        intro_content: Intro of the task,
            is empty when task has no sub-questions; its content is in ExamSubtask.
        intro_screen: Task introduction screen,
            is empty when task has no sub-questions; its content is in ExamSubtask.
        start_page: Page where the task begins.
        end_page: Page where the task ends.
        solution_start_page: Page where the task solution begins.
        solution_end_page: Page where the task solution ends.
    """

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="tasks")
    number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_("Number"),
    )
    intro_content = models.TextField(
        blank=True,
        help_text=_("The extracted content of the intro task from the PDF file."),
    )
    intro_screen = models.ImageField(
        upload_to="examtask/images",
        verbose_name=_("Task intro screen"),
        blank=True,
        editable=False,
    )
    start_page = models.PositiveSmallIntegerField(
        editable=False,
        null=True,
        help_text=_("Exam task start page"),
    )
    end_page = models.PositiveSmallIntegerField(
        editable=False, null=True, help_text=_("Exam task end page")
    )
    solution_start_page = models.PositiveSmallIntegerField(
        editable=False,
        null=True,
        help_text=_("Exam task solution start page"),
    )
    solution_end_page = models.PositiveSmallIntegerField(
        editable=False,
        null=True,
        help_text=_("Exam task solution end page"),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["exam", "number"],
                name="exam_task_unique_number",
                violation_error_message=_(
                    "Exam task number already exists in this exam."
                ),
            ),
            models.CheckConstraint(
                condition=Q(
                    number__gte=1,
                ),
                name="exam_task_positive_number",
            ),
            models.CheckConstraint(
                condition=Q(
                    start_page__gte=1,
                ),
                name="exam_task_positive_start_page",
            ),
            models.CheckConstraint(
                condition=Q(
                    solution_start_page__gte=1,
                ),
                name="exam_task_positive_solution_start_page",
            ),
            models.CheckConstraint(
                condition=Q(
                    start_page__lte=F("end_page"),
                ),
                name="exam_task_valid_start_page_end_page",
            ),
            models.CheckConstraint(
                condition=Q(
                    solution_start_page__lte=F("solution_end_page"),
                ),
                name="exam_task_valid_solution_start_page_solution_end_page",
            ),
        ]
        verbose_name = _("Exam Task")
        verbose_name_plural = _("Exam Tasks")
        ordering = ["exam", "number"]

    def __str__(self) -> str:
        """
        Return a human-readable description of the exam task.

        Returns:
            A string such as "Mathematics 2023 Matriculation Exam 2024 August - extended - Task 1"
        """
        return f"{self.exam} – Task {self.number}"


class ExamSubtask(models.Model):
    exam_task = models.ForeignKey(
        ExamTask,
        on_delete=models.CASCADE,
        related_name="subtasks",
    )

    subnumber = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name=_("Subnumber"),
    )
    instruction_content = models.TextField(
        blank=True,
        help_text=_(
            "The extracted content of the instruction of the  sub task from the PDF file."
        ),
    )

    instruction_screen = models.ImageField(
        upload_to="examtask/images",
        verbose_name=_("Subtask instruction screen"),
        blank=True,
        editable=False,
    )

    solution_screen = models.ImageField(
        upload_to="examtask/images",
        verbose_name=_("Subtask solution screen"),
        blank=True,
        editable=False,
    )

    topics = models.ManyToManyField(
        Topic,
        related_name="exam_subtasks",
        verbose_name=_("Topics"),
    )

    explanation_timestamp = models.ForeignKey(
        "videos.VideoTimestamp",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="exam_subtasks",
        verbose_name=_("Explanation timestamp"),
    )

    completed_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="UserExamSubtaskCompletion",
        blank=True,
        related_name=_("completed_exam_subtasks"),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["exam_task", "subnumber"],
                name="exam_subtask_unique_subnumber",
                violation_error_message=_(
                    "Exam sub task number already exists in this task."
                ),
                nulls_distinct=False,
            ),
            models.CheckConstraint(
                condition=Q(
                    subnumber__gte=1,
                ),
                name="exam_subtask_positive_subnumber",
            ),
        ]
        verbose_name = _("Exam Subtask")
        verbose_name_plural = _("Exam Subtasks")
        ordering = ["exam_task", "subnumber"]

    def __str__(self) -> str:
        if self.subnumber is not None:
            return f"{self.exam_task}.{self.subnumber}"

        return f"{self.exam_task}"


class UserExamSubtaskCompletion(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="User",
        related_name="exam_subtask_completions",
    )

    exam_subtask = models.ForeignKey(
        ExamSubtask,
        on_delete=models.CASCADE,
        related_name="exam_subtask_completions",
        verbose_name="Exam Subtask",
    )

    completed_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "exam_subtask"],
                name="user_exam_subtask_completion_unique_user_exam_subtask",
                violation_error_message="User already finished this subtask",
            )
        ]

        verbose_name = "User Exam Subtask Completion"
        verbose_name_plural = "User Exam Subtask Completions"

    def __str__(self) -> str:
        return f"{self.exam_subtask} - {self.user}"


class ExamTaskFragment(models.Model):
    fragment_type = models.IntegerField(
        choices=FragmentTypeChoices.choices,
        verbose_name="Fragment type",
    )

    exam_task = models.ForeignKey(
        ExamTask,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="fragments",
        verbose_name="Exam task",
    )

    exam_subtask = models.ForeignKey(
        ExamSubtask,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="fragments",
        verbose_name="Exam subtask",
    )

    page = models.PositiveSmallIntegerField(
        verbose_name="Page",
        help_text="The page containing the task or the solution",
    )

    y_start = models.FloatField(
        verbose_name="Y start",
        help_text="The start of the y position of the fragment in fraction from page height (0-1)",
    )

    y_end = models.FloatField(
        verbose_name="Y end",
        help_text="The end of the y position of the fragment in fraction from page height (0-1)",
    )

    order = models.PositiveSmallIntegerField(
        verbose_name="Order",
        help_text="Position of this fragment when fragments are stacked into one image. "
        "Numbered from 1 separately for each task/subtask and fragment type.",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["exam_task", "fragment_type", "order"],
                name="exam_task_fragment_unique_exam_task_fragment_type_order",
            ),
            models.UniqueConstraint(
                fields=["exam_subtask", "fragment_type", "order"],
                name="exam_task_fragment_unique_exam_subtask_fragment_type_order",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        fragment_type=FragmentTypeChoices.INTRO,
                        exam_task__isnull=False,
                        exam_subtask__isnull=True,
                    )
                    | Q(
                        fragment_type__in=[
                            FragmentTypeChoices.INSTRUCTION,
                            FragmentTypeChoices.SOLUTION,
                        ],
                        exam_task__isnull=True,
                        exam_subtask__isnull=False,
                    )
                ),
                name="exam_task_fragment_valid_fragment_type_exam_task_exam_subtask",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        y_start__gte=0,
                        y_start__lt=F("y_end"),
                        y_end__lte=1,
                    )
                ),
                name="exam_task_fragment_valid_y_start_y_end",
            ),
            models.CheckConstraint(
                condition=(Q(page__gte=1)), name="exam_task_fragment_positive_page"
            ),
            models.CheckConstraint(
                condition=(Q(order__gte=1)), name="exam_task_fragment_positive_order"
            ),
        ]
        verbose_name = "Exam Task Fragment"
        verbose_name_plural = "Exam Task Fragments"
        ordering = ["fragment_type", "order"]

    def __str__(self) -> str:
        """
        Return a human-readable description of the exam task fragment.

        Returns:
            A string such as "Mathematics ... – Instruction #1 (Page 4)"
        """
        owner = self.exam_task or self.exam_subtask

        return f"{owner} – {self.get_fragment_type_display()} #{self.order} (Page {self.page})"
