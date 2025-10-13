import os
import requests
import hashlib
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from analytics.models import Patient, Provider, Payer, Referral

# --- API Configuration ---
TOKEN_URL = "https://api.preview.platform.athenahealth.com/oauth2/v1/token"
API_BASE_URL = "https://api.preview.platform.athenahealth.com"
PRACTICE_ID = "195900"
# Reverted to only the single, known-working scope
SCOPE = "system/CarePlan.read"

class Command(BaseCommand):
    help = "Imports booked appointment data from the athenaOne v1 API."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of past days to fetch appointments for. Defaults to 7.",
        )

    def _get_token(self):
        self.stdout.write("Requesting token...")
        client_id = os.environ.get("ATHENA_CLIENT_ID")
        client_secret = os.environ.get("ATHENA_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise CommandError("ATHENA_CLIENT_ID and ATHENA_CLIENT_SECRET must be set.")

        payload = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': SCOPE,
        }
        try:
            response = requests.post(TOKEN_URL, data=payload)
            response.raise_for_status()
            token = response.json()['access_token']
            self.stdout.write(self.style.SUCCESS("Token received."))
            return token
        except requests.exceptions.HTTPError as e:
            raise CommandError(f"Token request failed: {e.response.text}")

    def _get_department_id(self, token):
        self.stdout.write("Fetching department ID...")
        url = f"{API_BASE_URL}/v1/{PRACTICE_ID}/departments"
        headers = {'Authorization': f'Bearer {token}'}
        params = {'limit': 1}
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            department_id = response.json()['departments'][0]['departmentid']
            self.stdout.write(self.style.SUCCESS(f"Using Department ID: {department_id}"))
            return department_id
        except (requests.exceptions.HTTPError, KeyError, IndexError) as e:
            raise CommandError(f"Could not fetch department ID: {e}")

    def handle(self, *args, **opts):
        days = opts["days"]
        access_token = self._get_token()
        department_id = self._get_department_id(access_token)

        self.stdout.write(f"Fetching booked appointments for the last {days} days...")
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        url = f"{API_BASE_URL}/v1/{PRACTICE_ID}/appointments/booked"
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {
            'departmentid': department_id,
            'startdate': start_date,
            'enddate': end_date,
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            appointments = response.json().get("appointments", [])
        except requests.exceptions.HTTPError as e:
            raise CommandError(f"Error fetching appointments: {e.response.text}")

        if not appointments:
            self.stdout.write(self.style.WARNING("No appointments found."))
            return

        created_count = 0
        for appt in appointments:
            patient_id = str(appt.get("patientid"))
            provider_id = str(appt.get("providerid"))
            appointment_date_str = appt.get("date")

            if not all([patient_id, provider_id, appointment_date_str]):
                continue

            # Convert API date (MM/DD/YYYY) to Django's required format (YYYY-MM-DD)
            try:
                appointment_date = datetime.strptime(appointment_date_str, "%m/%d/%Y").date()
            except ValueError:
                self.stdout.write(self.style.WARNING(f"Skipping appointment due to invalid date: {appointment_date_str}"))
                continue

            patient, _ = Patient.objects.get_or_create(
                original_id=patient_id,
                defaults={"pseudonym": hashlib.sha256(patient_id.encode()).hexdigest()},
            )

            # Use the limited provider info from the appointments endpoint
            provider_full_name = f"{appt.get('providerfirstname', '')} {appt.get('providerlastname', '')}".strip()
            if not provider_full_name:
                provider_full_name = f"Provider {provider_id}"

            provider, _ = Provider.objects.update_or_create(
                npi=provider_id, # Using providerid as a stand-in for NPI
                defaults={
                    "full_name": provider_full_name,
                    "specialty": appt.get("providerspecialty", "N/A"),
                },
            )

            _, created = Referral.objects.get_or_create(
                patient=patient,
                provider=provider,
                referral_date=appointment_date,
                status=Referral.Status.SCHEDULED,
                defaults={
                    "payer": None, # No payer info in this endpoint
                    "in_network": True,
                    "cost_value": 0,
                },
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Import complete. Found {len(appointments)} appointments, created {created_count} new referral records."
        ))