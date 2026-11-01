from courses.choices import SubjectChoices
from courses.models import Section
from django.db import models
from django.utils.translation import gettext_lazy as _
from examination_tasks.choices import LevelTypeChoices


def motif_image_path(instance, filename) -> str:
    """
    Method that returns the path of the motif image

    Args:
    instance: instance of the model
    filename: filename of the motif image
    Returns:
        Path of the motif image
    """
    return f"motifs/{instance.subject}/{instance.section.id}/{filename}"


class Motif(models.Model):
    subject = models.IntegerField(
        max_length=10,
        choices=SubjectChoices.choices,
        verbose_name=_("Subject"),
        default=1,
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="motifs",
        verbose_name=_("Section"),
    )
    level_type = models.IntegerField(
        choices=LevelTypeChoices.choices,
        null=True,
        blank=True,
        verbose_name=_("Level"),
        help_text=_("Motif level: basic or extended (Matriculation only)"),
    )

    content = models.CharField(
        max_length=255,
        verbose_name=_("Motif content"),
        help_text=_("Whole motif content"),
    )

    answer = models.TextField(
        verbose_name=_("answer"),
        help_text=_("Explanation about chosen motif"),
    )
    answer_picture = models.ImageField(
        upload_to=motif_image_path,
        blank=True,
        null=True,
        help_text=_("Motif explanation picture if needed"),
    )
    is_in_matriculation_sheets = models.BooleanField(
        default=False,
        verbose_name=_("If exists in matriculation sheets"),
    )

    is_mandatory = models.BooleanField(
        default=True,
        verbose_name=_("Mandatory for students"),
        help_text=_("Whether students must learn this motif"),
    )

    explanation_link = models.URLField(
        verbose_name=_("Link to explanation video"),
        help_text=_("Link to explanation video"),
    )

    class Meta:
        verbose_name = _("Motif")
        verbose_name_plural = _("Motifs")
        ordering = ["subject", "section", "level_type"]

    def __str__(self):
        level = self.get_level_type_display() if self.level_type else "No Level"
        return f"{self.get_subject_display()} - {self.section.name} - {level}: {self.content[:50]}"
