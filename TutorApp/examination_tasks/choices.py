from datetime import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _

current_year = datetime.now().year
YEAR_CHOICES = [(y, str(y)) for y in range(2002, current_year + 1)]

MONTH_CHOICES = [
    (1, _("January")),
    (2, _("February")),
    (3, _("March")),
    (4, _("April")),
    (5, _("May")),
    (6, _("June")),
    (7, _("July")),
    (8, _("August")),
    (9, _("September")),
    (10, _("October")),
    (11, _("November")),
    (12, _("December")),
]

LEVEL_CHOICES = [
    (1, _("Basic")),
    (2, _("Extended")),
]


class ExamTypeChoices(models.IntegerChoices):
    MATRICULATION = 1, _("Matriculation Exam")
    EIGHTH_GRADE = 2, _("Eighth Grade Exam")


class FormulaChoices(models.IntegerChoices):
    MATRICULATION_FORMULA_2002_2004 = 1, _("2002 2004 Matriculation Exam")
    MATRICULATION_FORMULA_2005_2009 = 2, _("2005 2009 Matriculation Exam")
    MATRICULATION_FORMULA_2010_2014 = 3, _("2010 2014 Matriculation Exam")
    MATRICULATION_FORMULA_2015_2026 = 4, _("2015 2026 Matriculation Exam")
    MATRICULATION_FORMULA_2023 = 5, _("2023 Matriculation Exam")
    E8_2018 = 6, _("E8 2018 Exam")
    EXAM_BEFORE_E8_2002_2019 = 7, _("2002 2019 Before E8 Exam")


MATRICULATION_EXAM_FORMULAS = (
    FormulaChoices.MATRICULATION_FORMULA_2002_2004,
    FormulaChoices.MATRICULATION_FORMULA_2005_2009,
    FormulaChoices.MATRICULATION_FORMULA_2010_2014,
    FormulaChoices.MATRICULATION_FORMULA_2015_2026,
    FormulaChoices.MATRICULATION_FORMULA_2023,
)

E8_EXAM_FORMULAS = (
    FormulaChoices.E8_2018,
    FormulaChoices.EXAM_BEFORE_E8_2002_2019,
)


class FragmentTypeChoices(models.IntegerChoices):
    INTRO = 1, _("Intro")
    INSTRUCTION = 2, _("Instruction")
    SOLUTION = 3, _("Solution")
