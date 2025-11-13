from django import forms
from .models import Referral, Provider

class ReferralForm(forms.Form):
    patient_id = forms.CharField(label='Patient', max_length=120, required=True)
    specialty = forms.ChoiceField(
        label='Specialty',
        required=False,
        choices=[], # Will be populated dynamically
        help_text="Only Optional: specify specialty if provider isn't selected"
    )
    provider = forms.ModelChoiceField(
        queryset=Provider.objects.all(),
        required=True,
        empty_label="--- select provider ---",
        to_field_name="npi"
    )
    department = forms.ChoiceField(
        label='Department',
        required=True,
        choices=[], # Will be populated dynamically
        help_text="Select a department for the chosen provider."
    )
    patient_insurance_id = forms.CharField(label='Payer', max_length=64, required=False)
    ordertypeid = forms.IntegerField(
        label='Referral Order Type', 
        required=True,
        help_text="The specific clinical service being ordered. Used for billing and clinical documentation."
    )
    reasonid = forms.IntegerField(
        label='Appointment Visit Reason',
        required=True,
        help_text="The reason for the visit, used to find appropriate appointment slots."
    )
    is_urgent = forms.BooleanField(label='Is Urgent?', required=False) # Checkboxes don't need required=True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically populate specialty choices
        specialties = Provider.objects.values_list('specialty', flat=True).distinct().order_by('specialty')
        print(f"DEBUG: Specialties found: {list(specialties)}") # Debugging line
        # Add an empty choice at the beginning
        self.fields['specialty'].choices = [('', '--- select specialty ---')] + [(s, s) for s in specialties if s]
        print(f"DEBUG: Final specialty choices: {self.fields['specialty'].choices}") # Debugging line
    # cost_value = forms.DecimalField(label='Cost Value', max_digits=10, decimal_places=2)
    # status = forms.ChoiceField(label='Status', choices=Referral.Status.choices, initial=Referral.Status.PENDING)
