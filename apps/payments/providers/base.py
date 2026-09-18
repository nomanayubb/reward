"""Payment provider adapter interface (NOWPayments, EasyPaisa, ...).

Adapters own provider-specific API calls; the deposit/withdrawal services own
the business flow and the ledger.
"""
from abc import ABC
from dataclasses import dataclass, field
from decimal import Decimal


class ProviderConfigurationError(Exception):
    """Raised when a provider adapter is missing required configuration."""


class ProviderRequestError(Exception):
    """Raised when a provider API call fails (network or HTTP error)."""


@dataclass
class CreatedPayment:
    external_id: str
    status: str
    pay_address: str = ""
    pay_amount: Decimal | None = None
    pay_currency: str = ""
    instructions: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)


@dataclass
class PaymentStatusResult:
    external_id: str
    status: str
    amount: Decimal | None = None
    currency: str = ""
    raw: dict = field(default_factory=dict)


class PaymentProviderAdapter(ABC):
    code = "base"

    def __init__(self, provider, config: dict | None = None):
        self.provider = provider
        self.config = config if config is not None else (getattr(provider, "config", {}) or {})

    def create_payment(self, *, amount, currency: str, reference: str, user=None) -> CreatedPayment:
        raise NotImplementedError

    def check_payment(self, external_id: str) -> PaymentStatusResult:
        raise NotImplementedError

    def verify_webhook(self, payload: dict, headers: dict | None = None) -> bool:
        return False

    def parse_webhook(self, payload: dict, headers: dict | None = None) -> PaymentStatusResult:
        raise NotImplementedError

    def create_payout(self, *, amount, currency: str, destination: dict, reference: str) -> dict:
        raise NotImplementedError


def load_adapter(provider, config: dict | None = None) -> PaymentProviderAdapter:
    from django.utils.module_loading import import_string

    adapter_path = (getattr(provider, "config", {}) or {}).get("adapter_path")
    if not adapter_path:
        raise ValueError(f"PaymentProvider {provider.code} has no config.adapter_path")
    adapter_class = import_string(adapter_path)
    return adapter_class(provider, config=config)
