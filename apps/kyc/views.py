"""KYC page views."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView

from .forms import KYCForm
from .models import KYCVerification
from .services import KYCError, submit_verification


class KYCPageView(LoginRequiredMixin, TemplateView):
    """Server-rendered identity verification page."""

    template_name = "kyc/kyc.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("form", KYCForm())
        context["kyc"] = KYCVerification.objects.filter(user=self.request.user).first()
        return context

    def post(self, request, *args, **kwargs):
        form = KYCForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            try:
                submit_verification(
                    request.user,
                    full_name=data["full_name"],
                    date_of_birth=data.get("date_of_birth"),
                    country=data.get("country", ""),
                    address=data.get("address", ""),
                    document_type=data.get("document_type", ""),
                    document_number=data.get("document_number", ""),
                    document_front=data.get("document_front"),
                    document_back=data.get("document_back"),
                    selfie=data.get("selfie"),
                )
            except KYCError as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, "Submitted — your documents are under review.")
                return redirect("kyc-page")
        return self.render_to_response(self.get_context_data(form=form))
