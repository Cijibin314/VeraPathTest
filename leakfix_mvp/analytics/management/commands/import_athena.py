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
from leakfix_mvp.analytics.models import Patient, Provider, Payer, Referral, ImportLog

class Command(BaseCommand):
    help = "Incrementally imports appointment data from athenahealth."

    def add_arguments(self, parser):
        parser.add_argument("--practice_id", required=True, help="athenaOne practice ID")
        parser.add_argument("--client_id", required=True, help="athenaOne API client ID")
        parser.add_argument("--client_secret", required=True, help="athenaOne API client secret")

    def handle(self, *args, **opts):
        # Pre-run check
        initial_referral_count = Referral.objects.count()
        self.stdout.write(f"Pre-run check: Found {initial_referral_count} existing referrals.")
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
                    "scope": "athena/service/Athenanet.MDP.*",
                },
            )
            token_resp.raise_for_status()
            access_token = token_resp.json()["access_token"]
        except requests.RequestException as e:
            ImportLog.objects.create(task_name=task_name, last_run_at=current_run_time, status="failed", notes=f"Token Error: {e}")
            raise CommandError(f"Failed to obtain OAuth token: {e}")

        headers = {"Authorization": f"Bearer {access_token}"}

        # Step 2: Fetch appointment cancellation reasons for 'no-show' mapping
        noshow_reason_ids = set()
        try:
            cancel_reasons_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/appointmentcancelreasons"
            response = requests.get(cancel_reasons_url, headers=headers)
            response.raise_for_status()
            cancel_reasons_data = response.json()
            cancel_reasons = cancel_reasons_data.get('appointmentcancelreasons', [])
            for reason in cancel_reasons:
                if reason.get('noshow'):
                    noshow_reason_ids.add(str(reason.get('appointmentcancelreasonid')))
            self.stdout.write(self.style.SUCCESS(f"Found {len(noshow_reason_ids)} 'no-show' cancellation reason IDs."))
        except requests.RequestException as e:
            raise CommandError(f"Failed to fetch appointment cancel reasons: {e}")

        # Step 3: Fetch all providers and create them if they don't exist
        try:
            provider_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/providers"
            response = requests.get(provider_url, headers=headers)
            response.raise_for_status()
            providers_data = response.json().get("providers", [])

            provider_count = 0
            printed_first = False
            for provider_data in providers_data:
                provider_id = str(provider_data.get("providerid"))
                if not provider_id: continue

                if not printed_first:
                    self.stdout.write(f"[ATHENA_DEBUG] First provider ID from API: {provider_id}")
                    printed_first = True

                _, created = Provider.objects.update_or_create(
                    npi=provider_id, 
                    defaults={"full_name": provider_data.get("displayname") or f"Provider {provider_id}"}
                )
                if created:
                    provider_count += 1
            self.stdout.write(self.style.SUCCESS(f"Found and created {provider_count} new providers."))

        except requests.RequestException as e:
            raise CommandError(f"Failed to fetch providers: {e}")

        # Step 4: Fetch appointments in the determined time window
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

        # Step 5: Process the appointments
        created_count = 0
        updated_count = 0
        for appt_summary in all_appointments:
            appointment_id = str(appt_summary.get("appointmentid"))
            if not appointment_id:
                continue

            try:
                # Get detailed appointment data
                appt_detail_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/appointments/{appointment_id}"
                response = requests.get(appt_detail_url, headers=headers)
                response.raise_for_status()
                appt = response.json()[0]

                patient_id = str(appt.get("patientid"))
                provider_id = str(appt.get("providerid"))

                if not patient_id or not provider_id:
                    continue

                # Get patient details to store their name
                patient_details_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/patients/{patient_id}"
                response = requests.get(patient_details_url, headers=headers)
                response.raise_for_status()
                patient_data = response.json()[0]
                self.stdout.write(f"  -> Patient data from API: {patient_data}")

                patient, created = Patient.objects.get_or_create(
                    original_id=patient_id,
                )
                if created:
                    patient.save() # Ensure pseudonym is created

                patient.first_name = patient_data.get("firstname")
                patient.last_name = patient_data.get("lastname")
                patient.save()

                provider, _ = Provider.objects.get_or_create(
                    npi=provider_id, defaults={"full_name": f"Provider {provider_id}"}
                )

                ref_date_str = appt.get("date")
                if ref_date_str:
                    ref_date = datetime.strptime(ref_date_str, "%m/%d/%Y").date()
                else:
                    ref_date = timezone.now().date()

                # Determine Status
                status = Referral.Status.SCHEDULED  # Default for a booked appointment
                if appt.get('replacementappointmentid'):
                    status = Referral.Status.RESCHEDULED
                elif appt.get('appointmentstatus') == 'x': # Cancelled
                    cancel_reason_id = str(appt.get('appointmentcancellationreasonid'))
                    if cancel_reason_id in noshow_reason_ids:
                        status = Referral.Status.NO_SHOW
                    else:
                        status = Referral.Status.CANCELLED
                elif appt.get('appointmentstatus') in ['2', '3', '4']: # Checked-in, Checked-out, Charge Entered
                    status = Referral.Status.COMPLETED


                _, created = Referral.objects.update_or_create(
                    athena_appointment_id=appointment_id,
                    defaults={
                        "patient": patient,
                        "provider": provider,
                        "referral_date": ref_date,
                        "status": status,
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            except requests.RequestException as e:
                self.stdout.write(self.style.WARNING(f"Could not process appointment {appointment_id}: {e}"))
                continue

        # Step 6: Log the successful run
        ImportLog.objects.update_or_create(
            task_name=task_name,
            defaults={
                "last_run_at": current_run_time,
                "status": "success",
                "notes": f"Created {created_count} and updated {updated_count} referrals."
            }
        )
        self.stdout.write(self.style.SUCCESS(f"Import complete. Created {created_count} and updated {updated_count} referrals."))