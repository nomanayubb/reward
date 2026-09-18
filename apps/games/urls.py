"""Game routes (mounted under /api/v1/games/)."""
from django.urls import path

from .views import GameListView, GameSessionEndView, GameSessionEventView, GameSessionStartView

urlpatterns = [
    path("", GameListView.as_view(), name="game-list"),
    path("<slug:slug>/sessions/", GameSessionStartView.as_view(), name="game-session-start"),
    path("sessions/<str:token>/events/", GameSessionEventView.as_view(), name="game-session-event"),
    path("sessions/<str:token>/end/", GameSessionEndView.as_view(), name="game-session-end"),
]
