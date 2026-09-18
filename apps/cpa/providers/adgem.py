"""AdGem adapter — Offer API (REST) + Server-to-Server Postbacks (v3).

Built from AdGem's integration docs:
- Auth: exchange the dashboard **refresh token** at
  ``POST {api_base}/v1/users/token`` (form-encoded, OAuth 2.0) for a
  short-lived access token (~1 hour), then send it as ``Bearer`` on
  ``GET {api_base}/v1/offers``. Access tokens are cached until shortly before
  expiry.
- Postbacks v3: ``POST`` JSON ``{request_id, timestamp, data{...}}``; the
  ``Signature`` header is ``HMAC-SHA256(raw request body, postback key)`` in
  hex. We verify over the raw bytes.

Environment keys (never hard-coded):
    ADGEM_REFRESH_TOKEN  refresh token from dashboard → Properties & Apps
                         (ADGEM_API_KEY is accepted as an alias)
    ADGEM_POSTBACK_KEY   postback key (Postback Options; shown once)
    ADGEM_API_BASE       optional, defaults to https://offer-api.adgem.com

Compliance: AdGem requires **prior written consent** for incentivized traffic
(T&C §11.3). Imported offers get ``incentive_allowed`` from the provider
config (default False) — set it to True only after AdGem confirms in writing.
"""
import hashlib
import hmac
import json
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache

from .base import (
    CPAProviderAdapter,
    NormalizedConversion,
    NormalizedOffer,
    ProviderConfigurationError,
    ProviderRequestError,
)

DEFAULT_API_BASE = "https://offer-api.adgem.com"
DEFAULT_REPORT_BASE = "https://dashboard.adgem.com"
DEFAULT_TIMEOUT = 30
TOKEN_CACHE_KEY = "adgem:access_token"

# Cloudflare fronts AdGem's hosts and rejects unknown client signatures, so we
# identify as a normal HTTP client.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 RewardPlatform/1.0"
)


def _add_common_headers(request) -> None:
    request.add_header("User-Agent", USER_AGENT)
    request.add_header("Accept", "application/json")


def _header(headers: dict | None, name: str) -> str:
    for key, value in (headers or {}).items():
        if key.lower() == name.lower():
            return str(value)
    return ""


class AdgemAdapter(CPAProviderAdapter):
    code = "adgem"

    @property
    def refresh_token(self) -> str:
        return (
            getattr(settings, "ADGEM_REFRESH_TOKEN", "")
            or getattr(settings, "ADGEM_API_KEY", "")
            or ""
        )

    @property
    def postback_key(self) -> str:
        return getattr(settings, "ADGEM_POSTBACK_KEY", "") or ""

    @property
    def api_base(self) -> str:
        return (
            self.config.get("api_base")
            or getattr(settings, "ADGEM_API_BASE", "")
            or DEFAULT_API_BASE
        )

    # -- auth ---------------------------------------------------------------
    def _exchange_token(self) -> tuple[str, int]:
        """Exchange the refresh token for ``(access_token, expires_in)``."""
        if not self.refresh_token:
            raise ProviderConfigurationError(
                "ADGEM_REFRESH_TOKEN is not configured (dashboard → Properties & Apps)."
            )

        body = urllib.parse.urlencode(
            {"grant_type": "refresh_token", "refresh_token": self.refresh_token}
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.api_base.rstrip('/')}/v1/users/token", data=body, method="POST"
        )
        request.add_header("Content-Type", "application/x-www-form-urlencoded")
        _add_common_headers(request)

        try:
            with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT) as response:
                payload = json.loads(response.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as exc:
            detail = exc.read()[:300]
            raise ProviderRequestError(f"AdGem token exchange HTTP {exc.code}: {detail!r}") from exc
        except urllib.error.URLError as exc:
            raise ProviderRequestError(f"AdGem unreachable: {exc.reason}") from exc

        access_token = payload.get("access_token", "")
        if not access_token:
            raise ProviderRequestError("AdGem token exchange returned no access_token.")
        return access_token, int(payload.get("expires_in", 3600))

    def _get_access_token(self) -> str:
        token = cache.get(TOKEN_CACHE_KEY)
        if token:
            return token
        access_token, expires_in = self._exchange_token()
        # Refresh a little before the real expiry.
        cache.set(TOKEN_CACHE_KEY, access_token, max(60, expires_in - 300))
        return access_token

    # -- HTTP ---------------------------------------------------------------
    def _request(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.api_base.rstrip('/')}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        request = urllib.request.Request(url, method="GET")
        request.add_header("Authorization", f"Bearer {self._get_access_token()}")
        _add_common_headers(request)

        try:
            with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT) as response:
                return json.loads(response.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                cache.delete(TOKEN_CACHE_KEY)  # token expired — refresh next call
            detail = exc.read()[:300]
            raise ProviderRequestError(f"AdGem HTTP {exc.code}: {detail!r}") from exc
        except urllib.error.URLError as exc:
            raise ProviderRequestError(f"AdGem unreachable: {exc.reason}") from exc

    # -- reporting API ------------------------------------------------------
    @property
    def report_token(self) -> str:
        return (
            getattr(settings, "ADGEM_REPORT_TOKEN", "")
            or getattr(settings, "ADGEM_API_KEY", "")
            or ""
        )

    @property
    def report_base(self) -> str:
        return (
            self.config.get("report_base")
            or getattr(settings, "ADGEM_REPORT_BASE", "")
            or DEFAULT_REPORT_BASE
        )

    def _report_request(self, params: list[tuple]) -> list[dict]:
        if not self.report_token:
            raise ProviderConfigurationError(
                "ADGEM_REPORT_TOKEN is not configured (dashboard → generate API token)."
            )
        url = f"{self.report_base.rstrip('/')}/v1/report?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, method="GET")
        request.add_header("Authorization", f"Bearer {self.report_token}")
        _add_common_headers(request)

        try:
            with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT) as response:
                data = json.loads(response.read().decode("utf-8") or "[]")
        except urllib.error.HTTPError as exc:
            detail = exc.read()[:300]
            raise ProviderRequestError(f"AdGem report HTTP {exc.code}: {detail!r}") from exc
        except urllib.error.URLError as exc:
            raise ProviderRequestError(f"AdGem unreachable: {exc.reason}") from exc

        return data if isinstance(data, list) else data.get("data", [])

    def get_reporting_data(self, since=None, until=None) -> list[dict]:
        """Daily report rows (app_id, date, conversions, payout, ...).

        Used for reconciliation: compare their reported conversions/payout
        against our own ``OfferConversion`` rows for the same period.
        """
        params = [("group_by[]", "app_id"), ("group_by[]", "date")]
        if since is not None:
            params.append(("date_range[start_date]", since.strftime("%Y-%m-%d %H:%M:%S")))
        if until is not None:
            params.append(("date_range[end_date]", until.strftime("%Y-%m-%d %H:%M:%S")))
        return self._report_request(params)

    # -- provider interface -------------------------------------------------
    def get_offers(self) -> list[NormalizedOffer]:
        payload = self._request("/v1/offers")
        data = payload.get("data", payload)
        raw_offers = data.get("offers", []) if isinstance(data, dict) else (data or [])
        return [self._normalize_offer(item) for item in raw_offers]

    def _normalize_offer(self, item: dict) -> NormalizedOffer:
        creatives = item.get("creatives") or {}
        links = item.get("links") or {}
        geo = item.get("geo_targeting") or {}
        os_targeting = item.get("os_targeting") or []

        countries = [
            country.get("iso_alpha2")
            for country in (geo.get("countries") or [])
            if country.get("iso_alpha2")
        ]
        operating_systems = [entry.get("name") for entry in os_targeting if entry.get("name")]

        description = creatives.get("description") or ""
        instructions = creatives.get("instructions") or []
        if instructions:
            description = f"{description}\n" + "\n".join(f"• {line}" for line in instructions)

        categories = creatives.get("categories") or []

        return NormalizedOffer(
            external_id=str(item.get("id", "")),
            title=creatives.get("name") or item.get("name", ""),
            payout=Decimal(str(item.get("total_payout_usd", "0") or "0")),
            description=description.strip(),
            category=item.get("campaign_vertical") or (categories[0] if categories else ""),
            tracking_url=links.get("click_url", ""),
            preview_image=creatives.get("icon_url", ""),
            countries=countries,
            devices=item.get("device_targeting") or [],
            operating_systems=operating_systems,
            incentive_allowed=bool(self.config.get("incentive_allowed", False)),
            multiple_completion_allowed=bool(item.get("is_multi_reward", False)),
            reinstall_allowed=False,
            vpn_allowed=False,
            daily_user_limit=int(self.config.get("daily_user_limit", 1)),
            lifetime_user_limit=int(self.config.get("lifetime_user_limit", 1)),
            raw=item,
        )

    def track_click(self, offer, user, click_id: str, request=None) -> str:
        url = offer.tracking_url or ""
        if not url:
            return ""
        # AdGem's click URL carries a {playerid} placeholder.
        return url.replace("{playerid}", click_id).replace("{player_id}", click_id)

    def validate_signature(
        self, payload: dict, headers: dict | None = None, raw_body: bytes | None = None
    ) -> bool:
        key = self.postback_key
        if not key:
            return False
        signature = _header(headers, "Signature")
        if not signature:
            return False
        body = raw_body if raw_body is not None else json.dumps(payload).encode("utf-8")
        expected = hmac.new(key.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def process_postback(
        self, payload: dict, headers: dict | None = None, raw_body: bytes | None = None
    ) -> NormalizedConversion:
        data = payload.get("data") or {}
        conversion_type = str(data.get("conversion_type", "")).lower()
        approved = conversion_type == "reward"  # "install" postbacks are tracking-only

        return NormalizedConversion(
            external_conversion_id=str(data.get("conversion_id", "")),
            user_identifier=str(data.get("player_id", "")),
            payout=Decimal(str(data.get("payout", "0") or "0")),
            status="approved" if approved else "rejected",
            offer_external_id=str(data.get("offer_id", "")),
            reason="" if approved else f"conversion_type={conversion_type or 'unknown'}",
            raw=payload,
        )
