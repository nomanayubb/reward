"""Survey API views and the surveys page."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Survey
from .serializers import SurveySerializer


class SurveyListView(ListAPIView):
    serializer_class = SurveySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from apps.adminpanel.settings import get_setting

        if not get_setting("SURVEYS_ENABLED", True):
            return Survey.objects.none()
        return (
            Survey.objects.filter(status=Survey.Status.ACTIVE)
            .select_related("provider")
            .order_by("-payout")
        )


class SurveyListPageView(LoginRequiredMixin, ListView):
    """Server-rendered survey catalog."""

    template_name = "surveys/list.html"
    context_object_name = "surveys"

    def get_queryset(self):
        from apps.adminpanel.settings import get_setting

        if not get_setting("SURVEYS_ENABLED", True):
            return Survey.objects.none()
        return (
            Survey.objects.filter(status=Survey.Status.ACTIVE)
            .select_related("provider")
            .order_by("-payout")
        )
