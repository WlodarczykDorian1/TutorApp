import factory
from courses.tests.factories import SectionFactory
from factory.django import DjangoModelFactory

from .models import Motif


class MotifFactory(DjangoModelFactory):

    class Meta:
        model = Motif

    subject = factory.Iterator([1, 2])

    section = factory.SubFactory(SectionFactory)

    level_type = factory.Iterator([1, 2, None])

    content = factory.Faker("sentence", nb_words=6, locale="pl_PL")

    answer = factory.Faker("paragraph", nb_sentences=5, locale="pl_PL")

    answer_picture = None

    is_in_matriculation_sheets = False
    is_mandatory = True

    class Params:

        matriculation = factory.Trait(
            is_in_matriculation_sheets=True,
            level_type=1,
        )

        with_picture = factory.Trait(
            answer_picture=factory.django.ImageField(
                filename="test_motif.jpg", width=800, height=600, color="blue"
            )
        )
