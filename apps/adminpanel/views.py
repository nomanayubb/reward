"""Admin panel views: dashboard metrics and the withdrawal review queue."""
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView

from apps.deposits.models import Deposit
from apps.fraud.models import FraudEvent
from apps.offers.models import OfferConversion
from apps.rewards.models import Reward
from apps.surveys.models import SurveyCompletion
from apps.wallets.services import total_liability
from apps.withdrawals.models import Withdrawal
from apps.withdrawals.services import (
    WithdrawalError,
    approve_withdrawal,
    mark_paid,
    reject_withdrawal,
)

from .audit import log_action

OPEN_WITHDRAWAL_STATUSES = [
    Withdrawal.Status.REQUESTED,
    Withdrawal.Status.UNDER_REVIEW,
    Withdrawal.Status.APPROVED,
    Withdrawal.Status.PROCESSING,
]


class StaffRequiredMixin(UserPassesTestMixin):
    """Staff-only pages: 403 for logged-in non-staff, login redirect for guests."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Staff access required.")
        return super().handle_no_permission()


class AdminDashboardView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()

        conversions = OfferConversion.objects.exclude(status=OfferConversion.Status.REJECTED)
        surveys = SurveyCompletion.objects.exclude(status=SurveyCompletion.Status.REJECTED)

        context["users_total"] = self.request.user.__class__.objects.count()
        context["users_today"] = self.request.user.__class__.objects.filter(
            date_joined__date=today
        ).count()

        context["provider_revenue_usd"] = (
            conversions.aggregate(total=Sum("payout"))["total"] or 0
        ) + (surveys.aggregate(total=Sum("payout"))["total"] or 0)

        context["rewards_by_currency"] = (
            Reward.objects.exclude(status=Reward.Status.REJECTED)
            .values("currency")
            .annotate(total=Sum("user_reward"), count=Count("id"))
            .order_by("currency")
        )
        context["pending_rewards"] = Reward.objects.filter(
            status=Reward.Status.PENDING
        ).count()

        open_withdrawals = Withdrawal.objects.filter(status__in=OPEN_WITHDRAWAL_STATUSES)
        context["withdrawals_open"] = open_withdrawals.count()
        context["withdrawals_by_currency"] = (
            open_withdrawals.values("currency")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("currency")
        )

        context["deposits_today"] = (
            Deposit.objects.filter(status=Deposit.Status.CONFIRMED, confirmed_at__date=today)
            .values("currency")
            .annotate(total=Sum("amount"))
        )

        context["liability_pkr"] = total_liability("PKR")
        context["liability_usd"] = total_liability("USD")
        context["fraud_open"] = FraudEvent.objects.filter(
            status__in=[FraudEvent.Status.OPEN, FraudEvent.Status.REVIEWING]
        ).count()
        return context


class WithdrawalQueueView(StaffRequiredMixin, ListView):
    template_name = "adminpanel/withdrawals.html"
    context_object_name = "withdrawals"
    paginate_by = 50

    def get_queryset(self):
        queryset = (
            Withdrawal.objects.select_related("user", "method")
            .exclude(status__in=[Withdrawal.Status.PAID, Withdrawal.Status.REJECTED, Withdrawal.Status.CANCELLED])
            .order_by("requested_at")
        )
        status_filter = self.request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = Withdrawal.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        return context


class WithdrawalActionView(StaffRequiredMixin, View):
    """Approve / pay / reject a withdrawal with audit logging."""

    def post(self, request, pk):
        withdrawal = get_object_or_404(Withdrawal, pk=pk)
        action = request.POST.get("action", "")

        try:
            if action == "approve":
                approve_withdrawal(withdrawal, approved_by=request.user)
            elif action == "pay":
                mark_paid(withdrawal, reference=request.POST.get("reference", ""))
            elif action == "reject":
                reject_withdrawal(
                    withdrawal,
                    reason=request.POST.get("reason", ""),
                    rejected_by=request.user,
                )
            else:
                messages.error(request, "Unknown action.")
                return redirect("admin-withdrawals")
        except WithdrawalError as exc:
            messages.error(request, str(exc))
        else:
            log_action(
                actor=request.user,
                action=f"withdrawal.{action}",
                obj=withdrawal,
                reason=request.POST.get("reason", ""),
                request=request,
            )
            messages.success(request, f"Withdrawal {action} applied.")

        return redirect("admin-withdrawals")
