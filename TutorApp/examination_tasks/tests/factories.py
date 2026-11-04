import factory
from courses.choices import SubjectChoices
from examination_tasks.choices import (
    YEAR_CHOICES,
    ExamTypeChoices,
    FormulaChoices,
    LevelTypeChoices,
    MonthChoices,
)
from examination_tasks.models import Exam


class ExamFactory(factory.django.DjangoModelFactory):
    """
    Create an exam with files.

    By default, creates a new matriculation exam.
    Use the `e8` trait to create an eighth grade exam.
    """

    class Meta:
        model = Exam

    class Params:
        e8 = factory.Trait(
            exam_type=ExamTypeChoices.EIGHTH_GRADE,
            level_type=None,
            formula=FormulaChoices.E8_2018,
        )

    exam_type = ExamTypeChoices.MATRICULATION
    formula = FormulaChoices.MATRICULATION_FORMULA_2023
    level_type = LevelTypeChoices.BASIC
    subject = SubjectChoices.MATHEMATICS
    year = factory.Iterator(YEAR_CHOICES, getter=lambda choice: choice[0])
    month = MonthChoices.MAY
    tasks_file = factory.django.FileField(
        filename="tasks.pdf",
        data=b"fake content",
    )
    solutions_file = factory.django.FileField(
        filename="solutions.pdf",
        data=b"fake content",
    )
