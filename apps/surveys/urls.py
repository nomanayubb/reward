"""Survey routes (mounted under /api/v1/surveys/)."""
from django.urls import path

from .views import SurveyListView

urlpatterns = [
    path("", SurveyListView.as_view(), name="survey-list"),
]
