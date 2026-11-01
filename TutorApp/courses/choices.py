from django.db import models
from django.utils.translation import gettext_lazy as _


class SchoolLevelChoices(models.IntegerChoices):
    PRIMARY = 1, _("Primary School")
    SECONDARY = 2, _("Secondary School")


class DifficultyLevelChoices(models.IntegerChoices):
    EASY = 1, _("Easy")
    INTERMEDIATE = 2, _("Intermediate")
    ADVANCED = 3, _("Advanced")


class TaskSourceChoices(models.IntegerChoices):
    BOOK = 1, _("Book")
    WORKSHEET = 2, _("Worksheet/Generator")


class GradeChoices(models.IntegerChoices):
    PRIMARY_7 = 7, _("7th Grade - Primary")
    PRIMARY_8 = 8, _("8th Grade - Primary")
    SECONDARY_1 = 9, _("1st Year - Secondary")
    SECONDARY_2 = 10, _("2nd Year - Secondary")
    SECONDARY_3 = 11, _("3rd Year - Secondary")
    SECONDARY_4 = 12, _("4th Year - Secondary")


class SubjectChoices(models.IntegerChoices):
    MATHEMATICS = 1, _("Mathematics")
    PHYSICS = 2, _("Physics")


class BookTypeChoices(models.IntegerChoices):
    TEXTBOOK = 1, _("Textbook")
    TASK_COLLECTION = 2, _("Task Collection")
    WORK_CARDS = 3, _("Work Cards")
