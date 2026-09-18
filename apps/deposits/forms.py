"""Forms for the deposit page."""
from decimal import Decimal

from django import forms

from apps.payments.models import PaymentProvider


class DepositForm(forms.Form):
    provider = forms.ModelChoiceField(queryset=PaymentProvider.objects.none())
    amount = forms.DecimalField(min_value=Decimal("0.01"), max_digits=20, decimal_places=8)

    def __init__(self, *args, providers=None, **kwargs):
        super().__init__(*args, **kwargs)
        if providers is not None:
            self.fields["provider"].queryset = providers
