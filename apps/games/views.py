"""Game API views: catalog listing and the session lifecycle.

These endpoints are what the Game SDK calls. The client can report events and
a final score, but only ``end_session`` (server-side) can produce a reward.
"""
from django.shortcuts import get_object_or_404
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
