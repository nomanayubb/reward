"""Root URL configuration.

Web pages are rendered by each app's ``urls.py``; JSON APIs live under
``/api/v1/``. Provider callbacks live under ``/api/v1/webhooks/`` and
``/api/v1/postbacks/`` (see ``apps/api_urls.py``).
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.games.views import GameAssetView, GamePlayerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/v1/", include("apps.api_urls")),
    # Server-rendered pages
    path("", include("apps.users.web_urls")),
    path("accounts/", include("apps.accounts.web_urls")),
    path("wallet/", include("apps.wallets.web_urls")),
    path("transactions/", include("apps.ledger.web_urls")),
    path("games/", include("apps.games.web_urls")),
    path("offers/", include("apps.offers.web_urls")),
    path("surveys/", include("apps.surveys.web_urls")),
    path("withdraw/", include("apps.withdrawals.web_urls")),
    path("deposit/", include("apps.deposits.web_urls")),
    path("alerts/", include("apps.notifications.web_urls")),
    path("kyc/", include("apps.kyc.web_urls")),
    path("admin-panel/", include("apps.adminpanel.web_urls")),
    path("ads/", include("apps.advertising.urls")),
    # Game hosting
    path("play/<slug:slug>/", GamePlayerView.as_view(), name="game-player"),
    path("games/<slug:slug>/<path:asset>", GameAssetView.as_view(), name="game-asset"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
