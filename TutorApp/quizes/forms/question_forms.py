from core.forms import TypedChoiceMixin
from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.utils.translation import gettext_lazy as _
from examination_tasks.choices import LevelTypeChoices

from ..models import Answer, Question


class QuestionForm(TypedChoiceMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["level_type"] = self._make_typed_choice(
            LevelTypeChoices, _("Level Type")
        )

    class Meta:
        model = Question
        fields = ["text", "level_type", "picture", "explanation", "explanation_picture"]
        labels = {
            "text": _("Question Content"),
            "level_type": _("Level Type"),
            "picture": _("Illustration for the question"),
            "explanation": _("Explanation To The Question"),
            "explanation_picture": _("Explanation By Illustration To The Question"),
        }
        widgets = {
            "text": forms.Textarea(attrs={"placeholder": " "}),
            "explanation": forms.Textarea(attrs={"placeholder": " "}),
        }


class BaseAnswerFormSet(BaseInlineFormSet):
    def clean(self) -> None:
        """
        A method that prevents the form from being submitted with empty fields and checks whether at least one answer is correct
        """
        super().clean()

        if any(self.errors):
            return

        correct_answers_count = 0

        for form in self.forms:

            if not form.cleaned_data:
                continue

            text = form.cleaned_data["text"]

            if not text:
                continue

            if form.cleaned_data.get("DELETE"):
                continue

            if form.cleaned_data["is_correct"]:
                correct_answers_count += 1

        if correct_answers_count < 1:
            raise ValidationError(_("At least one answer must be marked as correct."))


AnswerFormSet = inlineformset_factory(
    Question,
    Answer,
    fields=["text", "is_correct"],
    extra=4,
    formset=BaseAnswerFormSet,
    labels={"text": _("Enter Answer")},
    widgets={
        "text": forms.TextInput(attrs={"placeholder": " "}),
    },
)
