"""Offer API views and the offers page.

The list endpoints return only offers the requesting user is actually
eligible for, using the shared eligibility engine (DRD §18). Serializers never
expose tracking URLs or internal flags.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .eligibility import evaluate_offer
from .models import Offer
from .serializers import OfferSerializer


class OfferListView(ListAPIView):
    serializer_class = OfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Offer.objects.filter(status=Offer.Status.ACTIVE, incentive_allowed=True)
            .select_related("provider", "category", "quota")
            .order_by("-rank_score", "-payout")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        offers = page if page is not None else list(queryset)

        country = getattr(request.user, "country", "") or ""
        eligible = [
            offer
            for offer in offers
            if evaluate_offer(request.user, offer, context={"country": country}).is_eligible
        ]

        serializer = self.get_serializer(eligible, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class OfferListPageView(LoginRequiredMixin, TemplateView):
    """Server-rendered eligible-offer catalog."""

    template_name = "offers/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        country = getattr(user, "country", "") or ""

        candidates = (
            Offer.objects.filter(status=Offer.Status.ACTIVE, incentive_allowed=True)
            .select_related("provider", "category", "quota")
            .order_by("-rank_score", "-payout")[:100]
        )
        context["offers"] = [
            offer
            for offer in candidates
            if evaluate_offer(user, offer, context={"country": country}).is_eligible
        ]
        return context
