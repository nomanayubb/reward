"""API v1 router — mounts every module's URLs under /api/v1/.

Provider callbacks are mounted at /api/v1/postbacks/ and /api/v1/webhooks/.
"""
from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.accounts.urls")),
    path("users/", include("apps.users.urls")),
    path("wallets/", include("apps.wallets.urls")),
    path("ledger/", include("apps.ledger.urls")),
    path("rewards/", include("apps.rewards.urls")),
    path("payments/", include("apps.payments.urls")),
    path("deposits/", include("apps.deposits.urls")),
    path("withdrawals/", include("apps.withdrawals.urls")),
    path("games/", include("apps.games.urls")),
    path("surveys/", include("apps.surveys.urls")),
    path("offers/", include("apps.offers.urls")),
    path("cpa/", include("apps.cpa.urls")),
    path("advertising/", include("apps.advertising.urls")),
    path("bonuses/", include("apps.bonuses.urls")),
    path("referrals/", include("apps.referrals.urls")),
    path("fraud/", include("apps.fraud.urls")),
    path("risk/", include("apps.risk.urls")),
    path("kyc/", include("apps.kyc.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("automation/", include("apps.automation.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("reports/", include("apps.reports.urls")),
    path("cms/", include("apps.cms.urls")),
    path("seo/", include("apps.seo.urls")),
    path("support/", include("apps.support.urls")),
    path("adminpanel/", include("apps.adminpanel.urls")),
    path("postbacks/", include("apps.offers.postback_urls")),
    path("webhooks/", include("apps.payments.webhook_urls")),
]
