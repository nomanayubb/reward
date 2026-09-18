"""Forms for the withdrawal pages."""
from decimal import Decimal

from django import forms

from .models import WithdrawalMethod


class WithdrawForm(forms.Form):
    method = forms.ModelChoiceField(queryset=WithdrawalMethod.objects.none())
    amount = forms.DecimalField(min_value=Decimal("0.01"), max_digits=20, decimal_places=8)

    def __init__(self, *args, methods=None, **kwargs):
        super().__init__(*args, **kwargs)
        if methods is not None:
            self.fields["method"].queryset = methods


class WithdrawalMethodForm(forms.Form):
    type = forms.ChoiceField(choices=WithdrawalMethod.Type.choices)
    label = forms.CharField(required=False, max_length=80)
    account_number = forms.CharField(max_length=64, label="Account number / wallet address")
