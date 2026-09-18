"""Web page routes for the surveys module."""
from django.urls import path

from .views import SurveyListPageView

urlpatterns = [
    path("", SurveyListPageView.as_view(), name="survey-list-page"),
]
