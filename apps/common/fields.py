"""Shared field helpers.

Money must never be a float. All monetary values use PostgreSQL NUMERIC(20, 8)
which is exact for both fiat and crypto amounts.
"""
from decimal import Decimal

from django.db import models

MONEY_MAX_DIGITS = 20
MONEY_DECIMAL_PLACES = 8


def money_field(**kwargs):
    """Exact decimal field for money/points amounts.

    Nullable fields get no default (None), so "not configured" stays
    distinguishable from "configured as zero".
    """
    kwargs.setdefault("max_digits", MONEY_MAX_DIGITS)
    kwargs.setdefault("decimal_places", MONEY_DECIMAL_PLACES)
    if not kwargs.get("null", False):
        kwargs.setdefault("default", Decimal("0"))
    return models.DecimalField(**kwargs)


ZERO = Decimal("0")
