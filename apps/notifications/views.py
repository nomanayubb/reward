"""Notification API views and the notifications page."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer
from .services import mark_all_read, mark_read


class NotificationListView(ListAPIView):
    """The user's notifications. Optional filter: ``?unread=1``."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user).order_by("-created_at")
        unread = self.request.query_params.get("unread")
        if unread in {"1", "true", "True"}:
            queryset = queryset.filter(is_read=False)
        return queryset


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not Notification.objects.filter(user=request.user, pk=pk).exists():
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        mark_read(request.user, [pk])
        return Response({"ok": True})


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"marked_read": mark_all_read(request.user)})


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"unread": count})


class NotificationPageView(LoginRequiredMixin, ListView):
    """Server-rendered notification list."""

    template_name = "notifications/list.html"
    context_object_name = "notifications"
    paginate_by = 25

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")
