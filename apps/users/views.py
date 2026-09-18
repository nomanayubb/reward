"""User page views: the dashboard and the tabbed Earn hub."""
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.advertising.services import serve_ad
from apps.notifications.models import Notification
from apps.rewards.models import Reward
from apps.wallets.models import WalletAccount
from apps.wallets.services import get_wallet

ZERO = Decimal("0")

EARN_TABS = ("games", "offers", "surveys")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "users/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        wallet = get_wallet(user)

        by_type = {
            account.type: account.balance
            for account in wallet.accounts.filter(currency=wallet.currency)
        }
        context["wallet"] = wallet
        context["cash"] = by_type.get(WalletAccount.Type.CASH, ZERO)
        context["pending"] = by_type.get(WalletAccount.Type.PENDING, ZERO)
        context["locked"] = by_type.get(WalletAccount.Type.LOCKED, ZERO)
        context["points"] = next(
            (a.balance for a in wallet.accounts.all() if a.type == WalletAccount.Type.POINTS),
            ZERO,
        )
        context["recent_rewards"] = (
            Reward.objects.filter(user=user).order_by("-created_at")[:5]
        )
        context["unread_notifications"] = Notification.objects.filter(
            user=user, is_read=False
        ).count()
        context["ad_slot"] = serve_ad("dashboard", self.request)
        return context


class EarnHubView(LoginRequiredMixin, TemplateView):
    """Tabbed earning hub (games / offers / surveys) with all rules shown."""

    template_name = "users/earn.html"

    def get_context_data(self, **kwargs):
        from apps.games.services import catalog_rows as game_rows
        from apps.offers.services import catalog_rows as offer_rows
        from apps.offers.services import next_reset_at
        from apps.surveys.models import Survey

        context = super().get_context_data(**kwargs)
        tab = self.request.GET.get("tab", "games")
        context["tab"] = tab if tab in EARN_TABS else "games"

        user = self.request.user
        country = getattr(user, "country", "") or ""

        context["games"] = game_rows(user)
        context["offers"], context["unavailable"] = offer_rows(user, country)
        context["surveys"] = (
            Survey.objects.filter(status=Survey.Status.ACTIVE)
            .select_related("provider")
            .order_by("-payout")
        )
        context["next_reset_at"] = next_reset_at()
        context["ad_slot"] = serve_ad("dashboard", self.request)
        return context
