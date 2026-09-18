"""Forms for the admin panel."""
from decimal import Decimal

from django import forms

from apps.users.models import UserRestriction


class AdjustBalanceForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Positive credits the user, negative debits.",
    )
    currency = forms.ChoiceField(choices=[("PKR", "PKR"), ("USD", "USD")])
    reason = forms.CharField(max_length=255, required=True)

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount == Decimal("0"):
            raise forms.ValidationError("Amount must not be zero.")
        return amount


class RestrictionForm(forms.Form):
    type = forms.ChoiceField(choices=UserRestriction.Type.choices)
    reason = forms.CharField(max_length=255, required=False)


class FeatureFlagToggleForm(forms.Form):
    flag_id = forms.UUIDField()
