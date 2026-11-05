import factory
from courses.choices import SubjectChoices
from courses.models import Topic
from courses.tests.factories import TopicFactory
from examination_tasks.choices import (
    YEAR_CHOICES,
    ExamTypeChoices,
    FormulaChoices,
    LevelTypeChoices,
    MonthChoices,
)
from examination_tasks.models import Exam, ExamSubtask, ExamTask


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


class ExamTaskFactory(factory.django.DjangoModelFactory):
    """
    Create an ExamTask belonging to a new Exam.

    The default task represents a task without sub-questions, so
    intro_content and intro_screen are empty (its content lives in
    ExamSubtask). Page ranges are empty because no ExamTaskFragment
    exists yet; they are calculated from fragments, not set directly.

    No ExamSubtask is created automatically. Create subtasks explicitly
    with ExamSubtaskFactory(exam_task=...), so each test controls
    their number and subnumbers.

    Use the `e8` trait to create a task belonging to an eighth grade exam.
    """

    class Meta:
        model = ExamTask

    class Params:
        e8 = factory.Trait(
            exam=factory.SubFactory(ExamFactory, e8=True),
        )

    exam = factory.SubFactory(ExamFactory)
    number = factory.Sequence(lambda n: n + 1)


class ExamSubtaskFactory(factory.django.DjangoModelFactory):
    """
    Create an ExamSubtask belonging to a new ExamTask.

    By default, each subtask gets a unique, ascending subnumber
    (do not rely on its exact value).
    By default, each subtask gets a new topic from TopicFactory.
    You can pass your own topics but empty list will get subtask without any topic.
    Instruction_content is empty because PDF extraction is not run.
    Instruction_screen and solution_screen are empty because no
    ExamTaskFragment exists yet.


    Use the `e8` trait to create a subtask belonging to an eighth grade exam task.
    Use the `null_subnumber` trait to create the single subtask of a task
    without sub-questions. Only one such subtask is allowed per task
    (exam_subtask_unique_subnumber), so do not combine this trait with
    create_batch for the same exam_task.
    """

    class Meta:
        model = ExamSubtask

    class Params:
        e8 = factory.Trait(
            exam_task=factory.SubFactory(ExamTaskFactory, e8=True),
        )
        null_subnumber = factory.Trait(
            subnumber=None,
        )

    exam_task = factory.SubFactory(ExamTaskFactory)
    subnumber = factory.Sequence(lambda n: n + 1)

    @factory.post_generation
    def topics(self, create: bool, extracted: list[Topic] | None, **kwargs) -> None:
        """
        Attach topics to the exam subtask after it is saved.

        Args:
            create: True for .create(), False for .build().
            extracted: Topics passed by the test, or None if not passed.
            **kwargs: Extra arguments passed as topics__<name>=... (unused).
        """
        if not create:
            return

        if extracted is None:
            self.topics.add(TopicFactory())
            return

        self.topics.add(*extracted)
