"""
Management command to import appointments from athenaOne and create referrals.

Usage:
    python manage.py import_athena --practice_id=123 \
       --client_id=YOUR_CLIENT_ID --client_secret=YOUR_SECRET --days=7

This script will:
- Obtain an OAuth2 token via the client credentials grant.
- Fetch appointments for the specified date range via Athena’s Appointments API.
- Map each appointment to Patient, Provider, Payer, and Referral models.
- Create a Referral with status SCHEDULED and mark it in-network by default.
Adjust the in_network and cost_value logic to match your business rules.
"""
import hashlib
from datetime import datetime, timedelta
import requests
from django.core.management.base import BaseCommand, CommandError
from analytics.models import Patient, Provider, Payer, Referral

class Command(BaseCommand):
    help = "Import appointment data from athenahealth and create referrals."

    def add_arguments(self, parser):
        parser.add_argument("--practice_id", required=True, help="athenaOne practice ID")
        parser.add_argument("--client_id", required=True, help="athenaOne API client ID")
        parser.add_argument("--client_secret", required=True, help="athenaOne API client secret")
        parser.add_argument("--days", type=int, default=7, help="Number of future days to fetch appointments")

    def handle(self, *args, **opts):
        practice_id = opts["practice_id"]
        client_id = opts["client_id"]
        client_secret = opts["client_secret"]
        days = opts["days"]

        # Step 1: Authenticate with athena using OAuth2 client credentials.
        token_url = "https://api.preview.platform.athenahealth.com/oauth2/v1/token"
        try:
            token_resp = requests.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scope": "system/CarePlan.read",
                },
            )
            token_resp.raise_for_status()
        except requests.RequestException as e:
            raise CommandError(f"Failed to obtain OAuth token: {e}")

        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise CommandError("OAuth token response did not contain an access_token.")

        headers = {"Authorization": f"Bearer {access_token}"}

        # Step 2: Fetch appointments for the next N days.
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=days)
        appt_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/appointments"
        params = {
            "startdate": start_date.isoformat(),
            "enddate": end_date.isoformat(),
            "showcancelled": False,
            "showdeleted": False,
        }
        try:
            appt_resp = requests.get(appt_url, headers=headers, params=params)
            appt_resp.raise_for_status()
        except requests.RequestException as e:
            raise CommandError(f"Failed to fetch appointments: {e}")

        appointments = appt_resp.json().get("appointments", [])
        created_count = 0

        for appt in appointments:
            # Map patient
            patient_id = str(appt.get("patientid"))
            if not patient_id:
                continue
            pseudonym = hashlib.sha256(patient_id.encode()).hexdigest()
            patient, _ = Patient.objects.get_or_create(
                original_id=patient_id,
                defaults={"pseudonym": pseudonym},
            )

            # Map provider
            prov_info = appt.get("provider") or {}
            npi = str(prov_info.get("npi") or prov_info.get("providerid") or "")
            if not npi:
                continue
            full_name = prov_info.get("name") or f"Provider {npi}"
            specialty = prov_info.get("specialty") or ""
            provider, _ = Provider.objects.get_or_create(
                npi=npi,
                defaults={
                    "full_name": full_name,
                    "specialty": specialty,
                    "subspecialty": "",
                    "city": prov_info.get("city") or "",
                    "state": prov_info.get("state") or "",
                },
            )

            # Map payer (primary insurance)
            payer = None
            insurances = appt.get("patientinsurance") or []
            if insurances:
                primary = insurances[0]
                payer_code = str(primary.get("insurancepackageid"))
                payer_name = primary.get("insurancepackagename") or payer_code
                if payer_code:
                    payer, _ = Payer.objects.get_or_create(
                        code=payer_code,
                        defaults={"name": payer_name},
                    )

            # Create referral (avoid duplicates)
            ref_date = appt.get("appointmentdate")
            if not ref_date:
                continue
            _, created = Referral.objects.get_or_create(
                patient=patient,
                provider=provider,
                payer=payer,
                referral_date=ref_date,
                defaults={
                    "status": Referral.Status.SCHEDULED,
                    "in_network": True,  # TODO: compute real network status
                    "cost_value": 0,
                    "suggested_provider_ids": "",
                },
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Imported {created_count} new referrals from {start_date} to {end_date}."
        ))
