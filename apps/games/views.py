"""Game API views: catalog listing for the authenticated user."""
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Game
from .serializers import GameSerializer


class GameListView(ListAPIView):
    """Active games, ordered for display."""

    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Game.objects.filter(status=Game.Status.ACTIVE)
            .select_related("category")
            .order_by("sort_order", "title")
        )
