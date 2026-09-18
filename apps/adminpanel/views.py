"""Admin panel views: dashboard, withdrawal queue, users, settings, flags."""
import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView

from apps.deposits.models import Deposit
from apps.fraud.models import FraudEvent
from apps.offers.models import OfferConversion
from apps.rewards.models import Reward
from apps.surveys.models import SurveyCompletion
from apps.users.models import UserRestriction
from apps.wallets.services import adjust_balance, get_wallet, total_liability
from apps.withdrawals.models import Withdrawal
from apps.withdrawals.services import (
    WithdrawalError,
    approve_withdrawal,
    mark_paid,
    reject_withdrawal,
)

from .audit import log_action
from .forms import AdjustBalanceForm, RestrictionForm
from .models import ConfigurationVersion, FeatureFlag, PlatformSetting
from .settings import get_setting, set_setting

User = get_user_model()

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


class AdminUserListView(StaffRequiredMixin, ListView):
    template_name = "adminpanel/users.html"
    context_object_name = "users"
    paginate_by = 50

    def get_queryset(self):
        queryset = User.objects.order_by("-date_joined")
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(email__icontains=query)
                | Q(username__icontains=query)
                | Q(phone__icontains=query)
            )
        status_filter = self.request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["statuses"] = User.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        return context


class AdminUserDetailView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/user_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target = get_object_or_404(User, pk=self.kwargs["pk"])
        wallet = get_wallet(target)

        context["target"] = target
        context["wallet"] = wallet
        context["accounts"] = wallet.accounts.all()
        context["restrictions"] = target.restrictions.filter(is_active=True)
        context["rewards"] = Reward.objects.filter(user=target).order_by("-created_at")[:10]
        context["withdrawals"] = Withdrawal.objects.filter(user=target).order_by(
            "-requested_at"
        )[:10]
        context["adjust_form"] = AdjustBalanceForm()
        context["restriction_form"] = RestrictionForm()
        return context


class AdminUserActionView(StaffRequiredMixin, View):
    """Freeze/unfreeze, restrict/unrestrict and balance adjustments."""

    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk)
        action = request.POST.get("action", "")

        if action in {"freeze", "unfreeze"}:
            target.status = (
                User.Status.FROZEN if action == "freeze" else User.Status.ACTIVE
            )
            target.save(update_fields=["status", "updated_at"])
            log_action(actor=request.user, action=f"user.{action}", obj=target, request=request)
            messages.success(request, f"User {action}d.")

        elif action == "restrict":
            form = RestrictionForm(request.POST)
            if form.is_valid():
                UserRestriction.objects.update_or_create(
                    user=target,
                    type=form.cleaned_data["type"],
                    is_active=True,
                    defaults={"reason": form.cleaned_data.get("reason", "")},
                )
                log_action(
                    actor=request.user,
                    action="user.restrict",
                    obj=target,
                    new_value=form.cleaned_data["type"],
                    reason=form.cleaned_data.get("reason", ""),
                    request=request,
                )
                messages.success(request, "Restriction applied.")
            else:
                messages.error(request, "Invalid restriction form.")

        elif action == "unrestrict":
            UserRestriction.objects.filter(
                pk=request.POST.get("restriction_id"), user=target
            ).update(is_active=False)
            log_action(actor=request.user, action="user.unrestrict", obj=target, request=request)
            messages.success(request, "Restriction removed.")

        elif action == "adjust":
            form = AdjustBalanceForm(request.POST)
            if form.is_valid():
                try:
                    adjust_balance(
                        user=target,
                        amount=form.cleaned_data["amount"],
                        currency=form.cleaned_data["currency"],
                        reason=form.cleaned_data["reason"],
                        actor=request.user,
                    )
                except Exception as exc:  # ledger/service errors must be visible
                    messages.error(request, str(exc))
                else:
                    log_action(
                        actor=request.user,
                        action="wallet.adjust",
                        obj=target,
                        new_value=str(form.cleaned_data["amount"]),
                        reason=form.cleaned_data["reason"],
                        request=request,
                    )
                    messages.success(request, "Balance adjusted.")
            else:
                messages.error(request, "Invalid adjustment form.")
        else:
            messages.error(request, "Unknown action.")

        return redirect("admin-user-detail", pk=target.pk)


class AdminSettingsView(StaffRequiredMixin, TemplateView):
    """Runtime configuration center (PlatformSetting, versioned + audited)."""

    template_name = "adminpanel/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        groups: dict[str, list] = {}
        for setting in PlatformSetting.objects.order_by("group", "key"):
            groups.setdefault(setting.group, []).append(setting)
        context["groups"] = groups
        context["recent_changes"] = ConfigurationVersion.objects.order_by("-created_at")[:10]
        return context

    def post(self, request):
        key = request.POST.get("key", "").strip()
        raw = request.POST.get("value", "")
        if not key:
            messages.error(request, "Missing setting key.")
            return redirect("admin-settings")

        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw

        set_setting(key, value, updated_by=request.user, note="admin panel edit")
        log_action(
            actor=request.user,
            action="settings.update",
            object_type="PlatformSetting",
            object_id=key,
            new_value=value,
            request=request,
        )
        messages.success(request, f"Setting '{key}' updated.")
        return redirect("admin-settings")


class AdminFeatureFlagsView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/flags.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["flags"] = FeatureFlag.objects.order_by("key")
        return context

    def post(self, request):
        flag = get_object_or_404(FeatureFlag, pk=request.POST.get("flag_id"))
        flag.is_enabled = not flag.is_enabled
        flag.save(update_fields=["is_enabled", "updated_at"])
        log_action(
            actor=request.user,
            action="feature_flag.toggle",
            obj=flag,
            new_value=flag.is_enabled,
            request=request,
        )
        messages.success(request, f"{flag.key} is now {'on' if flag.is_enabled else 'off'}.")
        return redirect("admin-flags")


EMERGENCY_SWITCHES = [
    "GAMES_ENABLED",
    "OFFERS_ENABLED",
    "SURVEYS_ENABLED",
    "DEPOSITS_ENABLED",
    "WITHDRAWALS_ENABLED",
]


def _provider_model(kind: str):
    from apps.advertising.models import AdProvider
    from apps.cpa.models import CPAProvider
    from apps.payments.models import PaymentProvider
    from apps.surveys.models import SurveyProvider

    models = {
        "cpa": CPAProvider,
        "survey": SurveyProvider,
        "payment": PaymentProvider,
        "ad": AdProvider,
    }
    if kind not in models:
        raise Http404("Unknown provider kind.")
    return models[kind]


class AdminProvidersView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/providers.html"

    def get_context_data(self, **kwargs):
        from apps.advertising.models import AdProvider
        from apps.cpa.models import CPAProvider
        from apps.payments.models import PaymentProvider
        from apps.surveys.models import SurveyProvider

        context = super().get_context_data(**kwargs)
        context["cpa_providers"] = CPAProvider.objects.order_by("priority", "name")
        context["survey_providers"] = SurveyProvider.objects.order_by("priority", "name")
        context["payment_providers"] = PaymentProvider.objects.order_by("name")
        context["ad_providers"] = AdProvider.objects.order_by("name")
        context["switches"] = [
            {"key": key, "enabled": get_setting(key, True)} for key in EMERGENCY_SWITCHES
        ]
        return context


class AdminProviderActionView(StaffRequiredMixin, View):
    """Kill switches, per-provider toggles and manual syncs."""

    def post(self, request):
        action = request.POST.get("action", "")

        if action == "switch":
            key = request.POST.get("key", "")
            if key not in EMERGENCY_SWITCHES:
                messages.error(request, "Unknown switch.")
                return redirect("admin-providers")
            enabled = request.POST.get("value") == "on"
            set_setting(
                key,
                enabled,
                updated_by=request.user,
                group="switches",
                note="emergency switch",
            )
            log_action(
                actor=request.user,
                action="switch.toggle",
                object_type="PlatformSetting",
                object_id=key,
                new_value=enabled,
                request=request,
            )
            messages.success(request, f"{key} is now {'ON' if enabled else 'OFF'}.")

        elif action == "toggle_provider":
            model = _provider_model(request.POST.get("kind", ""))
            provider = get_object_or_404(model, pk=request.POST.get("provider_id"))
            provider.is_enabled = not provider.is_enabled
            provider.save(update_fields=["is_enabled", "updated_at"])
            log_action(
                actor=request.user,
                action="provider.toggle",
                obj=provider,
                new_value=provider.is_enabled,
                request=request,
            )
            messages.success(
                request,
                f"{provider.name} is now {'enabled' if provider.is_enabled else 'disabled'}.",
            )

        elif action == "sync":
            kind = request.POST.get("kind", "")
            try:
                if kind == "cpa":
                    from apps.offers.tasks import sync_offers

                    result = sync_offers()
                elif kind == "survey":
                    from apps.surveys.tasks import sync_surveys

                    result = sync_surveys()
                else:
                    raise ValueError("Unknown provider kind.")
            except Exception as exc:  # provider failures must be visible
                messages.error(request, f"Sync failed: {exc}")
            else:
                messages.success(request, f"Sync complete: {result}")

        else:
            messages.error(request, "Unknown action.")

        return redirect("admin-providers")


class AdminKYCQueueView(StaffRequiredMixin, ListView):
    template_name = "adminpanel/kyc.html"
    context_object_name = "verifications"
    paginate_by = 50

    def get_queryset(self):
        from apps.kyc.models import KYCVerification

        queryset = (
            KYCVerification.objects.select_related("user")
            .exclude(status=KYCVerification.Status.NOT_STARTED)
            .order_by("created_at")
        )
        status_filter = self.request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def get_context_data(self, **kwargs):
        from apps.kyc.models import KYCVerification

        context = super().get_context_data(**kwargs)
        context["statuses"] = KYCVerification.Status.choices
        return context


class AdminKYCActionView(StaffRequiredMixin, View):
    def post(self, request, pk):
        from apps.kyc.models import KYCVerification
        from apps.kyc.services import approve_verification, reject_verification

        kyc = get_object_or_404(KYCVerification, pk=pk)
        action = request.POST.get("action", "")

        if action == "approve":
            approve_verification(kyc, reviewer=request.user)
            log_action(actor=request.user, action="kyc.approve", obj=kyc, request=request)
            messages.success(request, "KYC approved.")
        elif action == "reject":
            reject_verification(
                kyc, reviewer=request.user, reason=request.POST.get("reason", "")
            )
            log_action(
                actor=request.user,
                action="kyc.reject",
                obj=kyc,
                reason=request.POST.get("reason", ""),
                request=request,
            )
            messages.success(request, "KYC rejected.")
        else:
            messages.error(request, "Unknown action.")

        return redirect("admin-kyc")
