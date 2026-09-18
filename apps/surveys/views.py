"""Survey API views: active survey catalog for the authenticated user."""
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Survey
from .serializers import SurveySerializer


class SurveyListView(ListAPIView):
    serializer_class = SurveySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Survey.objects.filter(status=Survey.Status.ACTIVE)
            .select_related("provider")
            .order_by("-payout")
        )
