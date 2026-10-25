from django.urls import path

from .views.exam_task_views import (
    AddExamTaskWizard,
    ExamTaskListView,
    TaskCutPdfStreamView,
    TaskDisplayView,
    TaskPdfView,
)

app_name = "examination_tasks"

urlpatterns = [
    path(
        "exams/tasks/add/",
        AddExamTaskWizard.as_view(),
        name="add_exam_task",
    ),
    path("tasks/<int:pk>/pdf/", TaskPdfView.as_view(), name="task-pdf"),
    path("tasks/<int:pk>/", TaskDisplayView.as_view(), name="task-display"),
    path(
        "tasks/<int:pk>/pdf-stream/",
        TaskCutPdfStreamView.as_view(),
        name="task-pdf-stream",
    ),
    path(
        "tasks/<int:pk>/pdf-stream/<str:kind>/",
        TaskCutPdfStreamView.as_view(),
        name="task-pdf-stream-kind",
    ),
    path(
        "exams/<int:exam_pk>/tasks/", ExamTaskListView.as_view(), name="exam_task_list"
    ),
]
