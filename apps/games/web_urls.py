"""Web page routes for the games module."""
from django.urls import path

from .views import GameListPageView

urlpatterns = [
    path("", GameListPageView.as_view(), name="game-list-page"),
]
