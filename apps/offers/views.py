"""Offer API views, the offers page and the click-through endpoint.

The list endpoints return only offers the requesting user is actually
eligible for, using the shared eligibility engine (DRD §18). Serializers never
expose tracking URLs or internal flags.
"""
import uuid

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .eligibility import evaluate_offer
from .models import Offer
from .serializers import OfferSerializer
from .services import catalog_rows, get_click_url, limit_status, next_reset_at, record_click


class OfferListView(ListAPIView):
    serializer_class = OfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from apps.adminpanel.settings import get_setting

        if not get_setting("OFFERS_ENABLED", True):
            return Offer.objects.none()
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
        from apps.adminpanel.settings import get_setting

        context = super().get_context_data(**kwargs)
        context["offers"] = []
        context["unavailable"] = []
        context["next_reset_at"] = next_reset_at()

        if not get_setting("OFFERS_ENABLED", True):
            return context

        country = getattr(self.request.user, "country", "") or ""
        context["offers"], context["unavailable"] = catalog_rows(self.request.user, country)
        return context


class OfferDetailView(LoginRequiredMixin, TemplateView):
    """Full offer page: reward, every campaign rule and the user's limits."""

    template_name = "offers/detail.html"

    def get_context_data(self, **kwargs):
        offer = get_object_or_404(Offer, pk=self.kwargs["pk"])
        user = self.request.user
        country = getattr(user, "country", "") or ""

        result = evaluate_offer(user, offer, context={"country": country})
        limits = limit_status(user, offer)

        context = super().get_context_data(**kwargs)
        context["row"] = {"offer": offer, "limits": limits, "reasons": result.reasons}
        context["next_reset_at"] = limits["next_reset_at"]
        context["eligible"] = result.is_eligible
        return context


class OfferStartView(LoginRequiredMixin, View):
    """Record a click and forward the user to the provider's tracking URL."""

    def get(self, request, pk):
        offer = get_object_or_404(Offer, pk=pk)
        country = getattr(request.user, "country", "") or ""

        eligibility = evaluate_offer(request.user, offer, context={"country": country})
        if not eligibility.is_eligible:
            messages.error(request, "This offer is not available for your account.")
            return redirect("offer-list-page")

        click_id = uuid.uuid4().hex
        click = record_click(
            request.user,
            offer,
            click_id=click_id,
            ip=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        url = get_click_url(request.user, offer, click)
        if not url:
            messages.error(request, "This offer has no tracking link configured yet.")
            return redirect("offer-list-page")

        return redirect(url)


class OfferwallIndexView(LoginRequiredMixin, TemplateView):
    """Hub of every enabled network's pre-built offerwall (network-agnostic)."""

    template_name = "offers/offerwall_index.html"

    def get_context_data(self, **kwargs):
        from .services import offerwall_urls

        context = super().get_context_data(**kwargs)
        context["offerwalls"] = offerwall_urls(self.request.user)
        return context


class OfferwallProviderView(LoginRequiredMixin, TemplateView):
    """Render one network's offerwall in an iframe (URL from its adapter)."""

    template_name = "offers/offerwall.html"

    def get_context_data(self, **kwargs):
        from apps.accounts.services import player_id_for
        from apps.cpa.models import CPAProvider

        from .services import offerwall_url

        context = super().get_context_data(**kwargs)
        provider = get_object_or_404(
            CPAProvider, code=self.kwargs["code"], is_enabled=True
        )
        url = offerwall_url(provider, self.request.user)
        if not url:
            raise Http404("This network has no offerwall configured.")

        context["provider"] = provider
        context["wall_url"] = url
        context["player_id"] = player_id_for(self.request.user)
        return context
