from django import forms
from .models import Referral, Provider

class ReferralForm(forms.Form):
    patient_id = forms.CharField(label='Patient ID', max_length=120)
    provider = forms.ModelChoiceField(
        queryset=Provider.objects.all(),
        required=False,
        empty_label="--- select provider ---"
    )
    specialty = forms.CharField(
        label='Specialty',
        max_length=120,
        required=False,
        help_text="Optional: specify specialty if provider isn't selected"
    )
    payer_code = forms.CharField(label='Payer Code', max_length=64, required=False)
    in_network = forms.BooleanField(label='In‑Network', required=False, initial=True)
    cost_value = forms.DecimalField(label='Cost Value', max_digits=10, decimal_places=2)
    status = forms.ChoiceField(label='Status', choices=Referral.Status.choices, initial=Referral.Status.PENDING)
