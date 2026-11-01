from django import template
from examination_tasks.choices import MonthChoices

from ..models import Exam

register = template.Library()


@register.filter
def get_month_display(month_number):
    return dict(MonthChoices).get(int(month_number), month_number)


@register.filter
def get_level_display(level_number):
    return dict(Exam.LEVEL_CHOICES).get(int(level_number), level_number)


@register.filter
def get_category_display(category_number):
    from ..models import ExamTask

    return dict(ExamTask._meta.get_field("category").choices).get(
        int(category_number), category_number
    )
