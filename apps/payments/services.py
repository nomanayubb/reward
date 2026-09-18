"""Payment/currency services: exchange rates and conversion (DRD §131).

The rate used for a transaction is stored on that transaction; historical
transactions are never recalculated with today's rate.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError

from apps.adminpanel.settings import get_setting

MONEY_QUANT = Decimal("0.00000001")


class ExchangeRateError(ValidationError):
    """Raised when no conversion path exists or the configured rate is invalid."""


def usd_to_pkr_rate() -> Decimal:
    """Admin-configured rate (PKR per 1 USD)."""
    return Decimal(str(get_setting("EXCHANGE_RATE_USD_PKR", "280.00")))


def convert(
    amount, from_currency: str, to_currency: str, *, rate: Decimal | None = None
) -> tuple[Decimal, Decimal]:
    """Convert between PKR and USD. Returns ``(converted_amount, rate_used)``."""
    amount = Decimal(str(amount))

    if from_currency == to_currency:
        return amount.quantize(MONEY_QUANT), Decimal("1")

    if {from_currency, to_currency} == {"USD", "PKR"}:
        usd_to_pkr = Decimal(str(rate)) if rate is not None else usd_to_pkr_rate()
        if usd_to_pkr <= 0:
            raise ExchangeRateError("EXCHANGE_RATE_USD_PKR must be positive.")
        if from_currency == "USD":
            return (amount * usd_to_pkr).quantize(MONEY_QUANT), usd_to_pkr
        return (amount / usd_to_pkr).quantize(MONEY_QUANT), usd_to_pkr

    raise ExchangeRateError(f"No conversion path from {from_currency} to {to_currency}.")
