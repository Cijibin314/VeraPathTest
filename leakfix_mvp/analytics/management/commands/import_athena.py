"""
Management command to incrementally import appointments from athenaOne.

This script fetches appointments that have been created or modified since the
last successful run, making it efficient for frequent, automated execution.

Usage:
    python manage.py import_athena --practice_id=123 \
       --client_id=YOUR_CLIENT_ID --client_secret=YOUR_SECRET
"""
import hashlib
from datetime import datetime, timedelta
import requests
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from analytics.models import Patient, Provider, Payer, Referral, ImportLog
from analytics.mock_data import generate_mock_creation_date

class Command(BaseCommand):
    help = "Incrementally imports appointment data from athenahealth."

    def add_arguments(self, parser):
        parser.add_argument("--practice_id", required=True, help="athenaOne practice ID")
        parser.add_argument("--client_id", required=True, help="athenaOne API client ID")
        parser.add_argument("--client_secret", required=True, help="athenaOne API client secret")

    def handle(self, *args, **opts):
        practice_id = opts["practice_id"]
        client_id = opts["client_id"]
        client_secret = opts["client_secret"]
        task_name = "import_athena_appointments"
        current_run_time = timezone.now()

        # Determine the time window for the query
        try:
            last_run = ImportLog.objects.filter(task_name=task_name, status="success").latest("last_run_at")
            start_date = last_run.last_run_at.date()
            self.stdout.write(f"Last successful run was on {start_date:%Y-%m-%d}. Fetching changes since then.")
        except ImportLog.DoesNotExist:
            start_date = (current_run_time - timedelta(days=30)).date()
            self.stdout.write("No previous successful run found. Fetching data for the last 30 days.")
        
        end_date = current_run_time.date()

        # Step 1: Authenticate
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
            access_token = token_resp.json()["access_token"]
        except requests.RequestException as e:
            ImportLog.objects.create(task_name=task_name, last_run_at=current_run_time, status="failed", notes=f"Token Error: {e}")
            raise CommandError(f"Failed to obtain OAuth token: {e}")

        headers = {"Authorization": f"Bearer {access_token}"}

        # Step 2: Fetch appointments in the determined time window
        try:
            all_appointments = []
            dept_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/departments"
            departments = requests.get(dept_url, headers=headers).json().get("departments", [])

            for dept in departments:
                department_id = dept['departmentid']
                self.stdout.write(f"Fetching appointments for Department ID: {department_id}...")
                
                params = {
                    "departmentid": department_id,
                    "startdate": start_date.isoformat(),
                    "enddate": end_date.isoformat(),
                }
                appt_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/appointments/booked"
                response = requests.get(appt_url, headers=headers, params=params)
                response.raise_for_status()
                all_appointments.extend(response.json().get("appointments", []))

            self.stdout.write(self.style.SUCCESS(f"Found {len(all_appointments)} total appointments to process."))

        except requests.RequestException as e:
            ImportLog.objects.create(task_name=task_name, last_run_at=current_run_time, status="failed", notes=f"API Error: {e}")
            raise CommandError(f"Failed to fetch appointments: {e}")

        # Step 3: Process the appointments
        created_count = 0
        for appt in all_appointments:
            patient_id = str(appt.get("patientid"))
            if not patient_id: continue

            patient, _ = Patient.objects.get_or_create(
                original_id=patient_id,
                defaults={"pseudonym": hashlib.sha256(patient_id.encode()).hexdigest()},
            )

            provider_id = str(appt.get("providerid") or "")
            if not provider_id: continue

            provider, _ = Provider.objects.update_or_create(
                npi=provider_id, defaults={"full_name": f"Provider {provider_id}"}
            )

            # If the API provides a date, use it. Otherwise, create a mock date.
            ref_date_str = appt.get("date")
            if ref_date_str:
                try:
                    ref_date = datetime.strptime(ref_date_str, "%m/%d/%Y").date()
                except ValueError:
                    self.stdout.write(self.style.WARNING(f"\n  -> Invalid date format '{ref_date_str}'. Using mock date."))
                    ref_date = generate_mock_creation_date()
            else:
                self.stdout.write(self.style.WARNING(f"\n  -> No creation date from API. Using mock date."))
                ref_date = generate_mock_creation_date()

            _, created = Referral.objects.update_or_create(
                patient=patient, provider=provider, referral_date=ref_date,
                defaults={"status": Referral.Status.PENDING} # Start all as pending
            )
            if created:
                created_count += 1

        # Step 4: Log the successful run
        ImportLog.objects.update_or_create(
            task_name=task_name,
            defaults={
                "last_run_at": current_run_time, 
                "status": "success",
                "notes": f"Imported {created_count} new referrals."
            }
        )
        self.stdout.write(self.style.SUCCESS(f"Import complete. Created {created_count} new referrals."))