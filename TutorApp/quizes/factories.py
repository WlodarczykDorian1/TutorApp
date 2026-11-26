import factory
from courses.tests.factories import SectionFactory
from examination_tasks.choices import LevelTypeChoices
from quizes.models import Answer, Question, Quiz


class QuizFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Quiz

    section = factory.SubFactory(SectionFactory)
    title = factory.Faker("sentence", nb_words=3)


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Question

    text = factory.Faker("text", max_nb_chars=250)
    quiz = factory.SubFactory(QuizFactory)
    level_type = factory.fuzzy.FuzzyChoice(choice[0] for choice in LevelTypeChoices)
    picture = None
    explanation = factory.Faker("text", max_nb_chars=250)
    explanation_picture = None


class AnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Answer

    question = factory.SubFactory(QuestionFactory)
    text = factory.Faker("text", max_nb_chars=100)
    is_correct = True
