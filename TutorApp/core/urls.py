"""TutorApp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "examination_tasks/",
        include("examination_tasks.urls", namespace="examination_tasks"),
    ),
    path("users/", include("users.urls", namespace="users")),
    path("quizes/", include("quizes.urls", namespace="quizes")),
    path("videos/", include("videos.urls", namespace="videos")),
    path("motifs/", include("motifs.urls", namespace="motifs")),
    path("select2/", include("django_select2.urls")),
    path("courses/", include("courses.urls", namespace="courses")),
    path("plans/", include("plans.urls", namespace="plans")),
    path("", RedirectView.as_view(pattern_name="users:login"), name="home"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]
    urlpatterns += debug_toolbar_urls()
