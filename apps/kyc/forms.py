"""Forms for the KYC page."""
from django import forms


class KYCForm(forms.Form):
    full_name = forms.CharField(max_length=160, label="Full name (as on document)")
    date_of_birth = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    country = forms.CharField(max_length=2, required=False, label="Country code (e.g. PK)")
    address = forms.CharField(max_length=255, required=False)
    document_type = forms.ChoiceField(
        required=False,
        choices=[
            ("", "— select —"),
            ("cnic", "CNIC"),
            ("passport", "Passport"),
            ("license", "Driving licence"),
        ],
    )
    document_number = forms.CharField(max_length=64, required=False)
    document_front = forms.FileField(required=False, label="Document (front)")
    document_back = forms.FileField(required=False, label="Document (back)")
    selfie = forms.FileField(required=False, label="Selfie holding document")
