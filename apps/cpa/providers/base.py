"""CPA provider adapter interface.

Every network implements this interface. The core reward engine only ever
sees ``NormalizedOffer`` / ``NormalizedConversion`` — never provider-specific
payloads (docs/DRD.md §91, §138, §246).
"""
from abc import ABC
from dataclasses import dataclass, field
from decimal import Decimal


class ProviderConfigurationError(Exception):
    """Raised when a provider adapter is missing required configuration."""


class ProviderRequestError(Exception):
    """Raised when a provider API call fails (network or HTTP error)."""


@dataclass
class NormalizedOffer:
    external_id: str
    title: str
    payout: Decimal
    description: str = ""
    category: str = ""
    tracking_url: str = ""
    preview_image: str = ""
    countries: list = field(default_factory=list)
    devices: list = field(default_factory=list)
    operating_systems: list = field(default_factory=list)
    incentive_allowed: bool = False
    multiple_completion_allowed: bool = False
    reinstall_allowed: bool = False
    vpn_allowed: bool = False
    daily_user_limit: int = 1
    lifetime_user_limit: int = 1
    expires_at: str | None = None
    raw: dict = field(default_factory=dict)


@dataclass
class NormalizedConversion:
    external_conversion_id: str
    user_identifier: str
    payout: Decimal
    status: str = "approved"
    offer_external_id: str = ""
    reason: str = ""
    raw: dict = field(default_factory=dict)


class CPAProviderAdapter(ABC):
    """Adapter base class. Override the methods the network supports."""

    code = "base"

    def __init__(self, provider, config: dict | None = None):
        self.provider = provider
        self.config = config if config is not None else (getattr(provider, "config", {}) or {})

    # -- capabilities ------------------------------------------------------
    def get_offers(self) -> list[NormalizedOffer]:
        raise NotImplementedError

    def track_click(self, offer, user, click_id: str, request=None) -> str:
        """Return the provider tracking URL for the user, or '' if unsupported."""
        return ""

    def process_postback(
        self, payload: dict, headers: dict | None = None, raw_body: bytes | None = None
    ) -> NormalizedConversion:
        raise NotImplementedError

    def validate_signature(
        self, payload: dict, headers: dict | None = None, raw_body: bytes | None = None
    ) -> bool:
        return True

    def validate_conversion(self, conversion: NormalizedConversion) -> bool:
        return conversion.status == "approved"

    def get_campaign_status(self, offer) -> dict:
        return {}

    def get_reporting_data(self, since=None, until=None) -> list[dict]:
        return []


def load_adapter(provider, config: dict | None = None) -> CPAProviderAdapter:
    from django.utils.module_loading import import_string

    adapter_class = import_string(provider.adapter_path)
    return adapter_class(provider, config=config)
