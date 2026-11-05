from courses.choices import GradeChoices, SchoolLevelChoices
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):

    school_type = models.IntegerField(choices=SchoolLevelChoices, null=True, blank=True)
    role = [(1, "Student"), (2, "Teacher"), (3, "Admin")]
    role_type = models.IntegerField(choices=role, default=1)

    grade = models.IntegerField(
        choices=GradeChoices.choices,
        null=True,
        blank=True,
        verbose_name="Grade",
        help_text="7-8 for primary, 9-12 for secondary",
    )

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return f"{self.username} - {self.role_type} - {self.grade}"
