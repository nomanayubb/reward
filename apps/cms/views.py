"""Public pages: landing page and CMS-driven static pages.

These are the pages a payment/CPA reviewer looks at (about, terms, privacy,
contact). Content is admin-authored in the CMS and rendered verbatim.
"""
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView

from .models import CMSPage


class PublicHomeView(TemplateView):
    """Landing page for visitors; logged-in users go to their dashboard."""

    template_name = "public/home.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().get(request, *args, **kwargs)


class CMSPageView(TemplateView):
    """Render a published CMS page (terms, privacy, about, contact, FAQ...)."""

    template_name = "public/page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = get_object_or_404(
            CMSPage, slug=self.kwargs["slug"], status=CMSPage.Status.PUBLISHED
        )
        return context
