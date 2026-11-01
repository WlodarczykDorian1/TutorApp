from typing import List, Optional

from courses.models import Section
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from examination_tasks.choices import LevelTypeChoices

SECONDS_PER_QUESTION: int = 15


class Quiz(models.Model):
    title = models.CharField(max_length=100)
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="quizzes",
        verbose_name="Section",
    )

    class Meta:
        verbose_name_plural = "Quizzes"
        ordering = ["section", "title"]

    def __str__(self):
        return f"{self.title} {self.section}"

    @property
    def is_primary_school(self) -> bool:
        """
        Property that checks if section is in primary school
        """
        return self.section.is_primary_school

    def get_last_attempt_for_user(
        self, user: AbstractBaseUser
    ) -> Optional["QuizAttempt"]:
        """
        Return the most recently completed attempt for the given user on this quiz.

        Args:
            user: The user whose attempt history should be checked.

        Returns:
            The latest completed QuizAttempt, or None if the user has never
            completed this quiz.
        """
        return QuizAttempt.objects.filter(
            quiz=self, user=user, completed_at__isnull=False
        ).first()

    def get_random_questions(
        self,
        number_of_questions: Optional[int] = None,
        level_type: Optional[int] = None,
    ) -> List["Question"]:
        """
        Return a list of randomly selected questions for quiz.

        Args:
            number_of_questions(Optional[int]): The number of questions to pick, if none all questions are taken
            level_type(Optional[int]): The level of question to pick, if none all levels are taken


        Returns:
            List of Question objects. Can be empty if the quiz has no questions,
            or if number_of_questions is None and no questions match the given level_type.

        Raises:
            ValueError:  Number of questions must be positive
            ValueError:  Number of questions must be lower or even to available questions

        """

        if level_type is not None:
            collection_of_questions = self.questions.filter(level_type=level_type)
        else:
            collection_of_questions = self.questions.all()

        if number_of_questions is not None:
            if number_of_questions <= 0:
                raise ValueError(_("Number of questions must be positive"))
            available_questions = collection_of_questions.count()

            if number_of_questions > available_questions:
                raise ValueError(
                    _(
                        "Cannot request %(requested)d questions. Only %(available)d available."
                    )
                    % {
                        "requested": number_of_questions,
                        "available": available_questions,
                    }
                )

        questions = collection_of_questions.order_by("?")
        questions = questions[:number_of_questions]

        return list(questions)


class Question(models.Model):
    text = models.TextField()
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Quiz",
    )
    level_type = models.IntegerField(
        choices=LevelTypeChoices,
        null=True,
        blank=True,
        help_text="Level of question. Can be Basic or Extended",
    )

    picture = models.ImageField(upload_to="question_picture/", blank=True, null=True)
    explanation = models.TextField(blank=True)
    explanation_picture = models.ImageField(
        upload_to="explanation_picture/", blank=True, null=True
    )

    def __str__(self):
        return f"{self.quiz.title} - {self.text[:50]}"


class Answer(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers"
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} ({'Correct' if self.is_correct else 'Incorrect'})"


class QuizAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    score = models.FloatField()
    max_score = models.IntegerField()
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-completed_at"]

    def __str__(self):
        return f"{self.user} - {self.quiz} - {self.score}/{self.max_score}"


class UserAnswer(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
    )
    selected_answers = models.ManyToManyField(
        Answer,
        related_name="user_quiz_answers",
    )
    points_earned = models.FloatField(default=0)

    class Meta:
        ordering = ["question__id"]
        unique_together = ["attempt", "question"]

    def __str__(self):
        return f"{self.attempt.user} - Q{self.question.id} - {self.points_earned}pts"
