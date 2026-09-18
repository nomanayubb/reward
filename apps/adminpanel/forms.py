"""Forms for the admin panel."""
import json
from decimal import Decimal

from django import forms

from apps.advertising.models import AdCampaign, AdProvider
from apps.payments.models import PaymentProvider
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
    """Create a direct/house ad campaign (banner, native, sponsorship, ...).

    ``html_snippet`` is for network tags (AdSense/Adsterra/...). It is only
    editable by staff, rendered verbatim on the page, and every save is
    audit-logged — never put user-supplied content here (ADR-013).
    """

    class Meta:
        model = AdCampaign
        fields = (
            "name",
            "provider",
            "ad_type",
            "image",
            "html_snippet",
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


class NetworkForm(forms.Form):
    """Add a CPA / survey / payment / ad provider from the admin panel."""

    KIND_CHOICES = [
        ("cpa", "CPA network"),
        ("survey", "Survey provider"),
        ("payment", "Payment provider"),
        ("ad", "Ad provider"),
    ]

    kind = forms.ChoiceField(choices=KIND_CHOICES)
    code = forms.SlugField(max_length=64, help_text="Unique id, e.g. adgem")
    name = forms.CharField(max_length=120)
    adapter_path = forms.CharField(
        max_length=255,
        required=False,
        help_text="Dotted path, e.g. apps.cpa.providers.adgem.AdGemAdapter",
    )
    priority = forms.IntegerField(min_value=0, initial=100)
    config = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
        help_text='JSON object, e.g. {"feed_url": "https://..."}',
    )
    is_enabled = forms.BooleanField(required=False)
    payment_kind = forms.ChoiceField(
        choices=PaymentProvider.Kind.choices, required=False, initial=PaymentProvider.Kind.LOCAL
    )
    supports_deposits = forms.BooleanField(required=False, initial=True)
    supports_withdrawals = forms.BooleanField(required=False)
    ad_kind = forms.ChoiceField(
        choices=AdProvider.Kind.choices, required=False, initial=AdProvider.Kind.DIRECT
    )

    def clean_config(self):
        raw = self.cleaned_data["config"].strip()
        if not raw:
            return {}
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise forms.ValidationError("Config must be a JSON object.")
        return value
