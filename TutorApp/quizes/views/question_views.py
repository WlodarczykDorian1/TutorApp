from typing import Any, Dict, Optional, Union

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from users.mixins import TeacherRequiredMixin

from ..forms.question_forms import AnswerFormSet, QuestionForm
from ..models import Question, Quiz, QuizAttempt, UserAnswer


class AddQuestion(TeacherRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = "quizes/add_question.html"

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        """Load the quiz from the URL or raise 404 if it doesn't exist."""
        super().setup(request, *args, **kwargs)
        self.quiz = get_object_or_404(Quiz, pk=kwargs["quiz_pk"])

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["formset"] = AnswerFormSet(self.request.POST)
        else:
            context["formset"] = AnswerFormSet()
        return context

    def form_valid(self, form: QuestionForm) -> HttpResponse:
        formset = AnswerFormSet(self.request.POST)

        if formset.is_valid():
            self.object = form.save(commit=False)
            self.object.quiz = self.quiz
            self.object.save()
            formset.instance = self.object
            formset.save()

            messages.success(self.request, _("Question has been successfully added."))

            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self) -> str:
        return reverse("quizes:add_question", kwargs={"quiz_pk": self.quiz.pk})


class QuestionReviewView(LoginRequiredMixin, DetailView):
    model = UserAnswer
    template_name = "quizes/question_review.html"
    context_object_name = "user_answer"

    def get_object(self, queryset: Optional[QuerySet[UserAnswer]] = None) -> UserAnswer:
        attempt_pk: int = self.kwargs["attempt_pk"]
        question_number: int = self.kwargs["question_number"]

        try:
            attempt: QuizAttempt = QuizAttempt.objects.get(
                pk=attempt_pk,
                user=self.request.user,
            )
        except QuizAttempt.DoesNotExist:
            raise Http404("There is no attempt in this quiz for this user")

        qs: QuerySet[UserAnswer] = (
            UserAnswer.objects.filter(attempt=attempt)
            .select_related("question")
            .prefetch_related(
                "selected_answers",
                "question__answers",
            )
            .order_by("question__id")
        )

        try:
            return qs[question_number - 1]
        except IndexError:
            raise Http404("There is no question in this attempt")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        user_answer = self.object

        context["correct_answers"] = user_answer.question.answers.filter(
            is_correct=True
        )

        question_number = self.kwargs["question_number"]
        total_questions = user_answer.attempt.answers.count()

        context["question_number"] = question_number
        context["total_questions"] = total_questions
        context["has_previous"] = question_number > 1
        context["has_next"] = question_number < total_questions
        context["attempt_pk"] = self.kwargs["attempt_pk"]
        context["previous_number"] = question_number - 1
        context["next_number"] = question_number + 1

        return context


class QuestionListView(TeacherRequiredMixin, ListView):
    model = Question
    template_name = "quizes/question_list.html"
    context_object_name = "questions"

    def get_queryset(self) -> QuerySet[Question]:
        self.quiz = get_object_or_404(Quiz, pk=self.kwargs["quiz_pk"])
        return self.quiz.questions.all()

    def get_context_data(self, *args, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["quiz"] = self.quiz
        return context


class QuestionDeleteView(TeacherRequiredMixin, DeleteView):
    model = Question
    template_name = "quizes/question_confirm_delete.html"
    context_object_name = "question"

    def get_success_url(self) -> Union[str, Promise]:
        return reverse_lazy(
            "quizes:question_list", kwargs={"quiz_pk": self.object.quiz.pk}
        )


class QuestionUpdateView(TeacherRequiredMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = "quizes/edit_question.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["formset"] = AnswerFormSet(
                instance=self.object, data=self.request.POST
            )
        else:
            context["formset"] = AnswerFormSet(instance=self.object)

        return context

    def form_valid(self, form: QuestionForm) -> HttpResponse:
        formset = AnswerFormSet(instance=self.object, data=self.request.POST)

        if formset.is_valid():

            self.object = form.save()

            formset.instance = self.object
            formset.save()

            messages.success(self.request, _("Question has been successfully updated."))

            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_success_url(self) -> Union[str, Promise]:
        return reverse_lazy(
            "quizes:question_list", kwargs={"quiz_pk": self.object.quiz.pk}
        )
