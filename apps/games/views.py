"""Game API views, the player page and development asset serving.

The API endpoints are what the Game SDK calls. The client can report events and
a final score, but only ``end_session`` (server-side) can produce a reward.
"""
from pathlib import Path

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Game, GameSession
from .serializers import GameSerializer, GameSessionSerializer
from .services import end_session, report_event, start_session


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


class GameSessionStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        game = get_object_or_404(Game, slug=slug, status=Game.Status.ACTIVE)
        try:
            session = start_session(
                request.user,
                game,
                ip=request.META.get("REMOTE_ADDR"),
                device_hash=request.data.get("device_id_hash", ""),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(GameSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class GameSessionEventView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        session = get_object_or_404(GameSession, session_token=token, user=request.user)
        try:
            event = report_event(
                session,
                event_type=request.data.get("type", ""),
                payload=request.data.get("payload") or {},
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"ok": True, "event_id": str(event.id)}, status=status.HTTP_201_CREATED)


class GameSessionEndView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        session = get_object_or_404(GameSession, session_token=token, user=request.user)

        score = request.data.get("score")
        if score is not None:
            try:
                score = int(score)
            except (TypeError, ValueError):
                return Response(
                    {"detail": "score must be an integer."}, status=status.HTTP_400_BAD_REQUEST
                )

        session = end_session(session, score=score)
        return Response(GameSessionSerializer(session).data)


class GamePlayerView(LoginRequiredMixin, TemplateView):
    """Hosts a game in an iframe with the Game Host script wired up.

    The game itself runs sandboxed; the host page owns the authenticated
    session and proxies SDK calls to the API.
    """

    template_name = "games/player.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game = get_object_or_404(
            Game, slug=self.kwargs["slug"], status=Game.Status.ACTIVE
        )
        context["game"] = game
        context["game_url"] = reverse(
            "game-asset", kwargs={"slug": game.slug, "asset": game.entry_path}
        )
        context["platform_origin"] = f"{self.request.scheme}://{self.request.get_host()}"
        context["user_data"] = {
            "username": self.request.user.username or "",
            "country": getattr(self.request.user, "country", ""),
        }
        context["config_data"] = {
            "min_session_seconds": game.min_session_seconds,
            "reward_rules_visible": True,
        }
        return context


class GameAssetView(View):
    """Serve files from ``games/<slug>/`` (development convenience).

    Production serves games from a separate origin (docs/GAME_INTEGRATION.md).
    Path traversal is blocked by resolving the final path and requiring it to
    stay inside the game folder.
    """

    def get(self, request, slug, asset):
        base = (Path(settings.GAMES_ROOT) / slug).resolve()
        if not base.is_dir():
            raise Http404("Game not found")

        target = (base / asset).resolve()
        if not target.is_relative_to(base) or not target.is_file():
            raise Http404("Asset not found")

        return FileResponse(target.open("rb"))
