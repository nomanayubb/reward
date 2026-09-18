"""Survey API views, the surveys page and the start endpoint."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Survey
from .serializers import SurveySerializer
from .services import start_session, survey_url


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


class SurveyStartView(LoginRequiredMixin, View):
    """Start a survey session and forward the user to the provider."""

    def get(self, request, pk):
        survey = get_object_or_404(Survey, pk=pk, status=Survey.Status.ACTIVE)
        session = start_session(request.user, survey, ip=request.META.get("REMOTE_ADDR"))

        try:
            url = survey_url(survey, request.user, session)
        except Exception:
            messages.error(request, "This survey is not connected to a provider yet.")
            return redirect("survey-list-page")

        if not url:
            messages.error(request, "This survey has no link configured yet.")
            return redirect("survey-list-page")

        return redirect(url)
