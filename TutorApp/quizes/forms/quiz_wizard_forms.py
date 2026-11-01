from django import forms
from django.utils.translation import gettext_lazy as _
from examination_tasks.choices import LevelTypeChoices

from ..models import Quiz


class QuizStepForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super().__init__(*args, **kwargs)
        answers = question.answers.all()
        self.fields["selected_answers"] = forms.MultipleChoiceField(
            choices=[(answer.id, answer.text) for answer in answers],
            widget=forms.CheckboxSelectMultiple,
            required=False,
        )


class QuizStartForm(forms.Form):
    QUESTION_CHOICES = [
        (10, _("10 questions")),
        (20, _("20 questions")),
        (50, _("50 questions")),
        ("all", _("All questions")),
    ]

    question_count = forms.ChoiceField(
        choices=QUESTION_CHOICES,
        widget=forms.Select,
        label=_("How many questions would you like?"),
        initial=10,
    )

    level_type = forms.ChoiceField(
        choices=LevelTypeChoices.choices,
        label=_("Level Type"),
        widget=forms.Select,
        initial=1,
    )

    def __init__(self, quiz: Quiz, *args, **kwargs):
        self.quiz = quiz
        super().__init__(*args, **kwargs)
        if quiz.is_primary_school:
            del self.fields["level_type"]

    def clean_question_count(self) -> str:
        question_count = self.cleaned_data["question_count"]
        available_questions = self.quiz.questions.count()

        if available_questions == 0:
            raise forms.ValidationError(
                _("This quiz has no questions yet. Cannot start!")
            )

        if question_count == "all":
            return question_count

        question_count_int = int(question_count)

        if available_questions < question_count_int:
            raise forms.ValidationError(
                _(
                    "This quiz has only %(available)d question(s). "
                    "You cannot select %(requested)d."
                )
                % {"available": available_questions, "requested": question_count_int}
            )

        return question_count
