"""Forms for the admin panel."""
from decimal import Decimal

from django import forms

from apps.advertising.models import AdCampaign
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


class AdCampaignForm(forms.ModelForm):
    """Create a direct/house ad campaign (banner, native, sponsorship, ...)."""

    class Meta:
        model = AdCampaign
        fields = (
            "name",
            "provider",
            "ad_type",
            "image",
            "target_url",
            "placements",
            "weight",
            "starts_at",
            "ends_at",
            "max_per_hour",
            "min_interval_minutes",
            "max_per_day",
        )
        widgets = {
            "starts_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "ends_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "placements": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["starts_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["ends_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["starts_at"].required = False
        self.fields["ends_at"].required = False
