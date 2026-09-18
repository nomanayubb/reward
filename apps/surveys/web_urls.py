"""Web page routes for the surveys module."""
from django.urls import path

from .views import SurveyListPageView, SurveyStartView

urlpatterns = [
    path("", SurveyListPageView.as_view(), name="survey-list-page"),
    path("<uuid:pk>/start/", SurveyStartView.as_view(), name="survey-start"),
]
