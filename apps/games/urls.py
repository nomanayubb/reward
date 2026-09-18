"""Game routes (mounted under /api/v1/games/)."""
from django.urls import path

from .views import GameListView

urlpatterns = [
    path("", GameListView.as_view(), name="game-list"),
]
