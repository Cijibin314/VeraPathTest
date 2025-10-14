"""
Management command to import appointments from athenaOne and create referrals.

Usage:
    python manage.py import_athena --practice_id=123 \
       --client_id=YOUR_CLIENT_ID --client_secret=YOUR_SECRET --days=7

This script will:
- Obtain an OAuth2 token via the client credentials grant.
- Fetch all department IDs.
- Loop through departments to find and fetch appointments.
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
        parser.add_argument("--days", type=int, default=7, help="Number of days to search for appointments")

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

        # Step 2: Get all departments
        self.stdout.write("Fetching all departments...")
        dept_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/departments"
        try:
            dept_resp = requests.get(dept_url, headers=headers)
            dept_resp.raise_for_status()
            departments = dept_resp.json().get('departments', [])
            if not departments:
                raise CommandError("No departments found for this practice.")
            self.stdout.write(self.style.SUCCESS(f"Found {len(departments)} departments."))
        except (requests.RequestException, KeyError, IndexError) as e:
            raise CommandError(f"Could not fetch departments: {e}")

        # Step 3: Loop through departments to find and fetch appointments
        appointments_found = False
        for dept in departments:
            department_id = dept['departmentid']
            self.stdout.write(f"Checking for appointments in Department ID: {department_id}...")

            start_date = datetime.now().date() - timedelta(days=days//2)
            end_date = datetime.now().date() + timedelta(days=days//2)
            appt_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/appointments/booked"
            params = {
                "departmentid": department_id,
                "startdate": start_date.isoformat(),
                "enddate": end_date.isoformat(),
                "showcancelled": False,
                "showdeleted": False,
            }
            try:
                appt_resp = requests.get(appt_url, headers=headers, params=params)
                appt_resp.raise_for_status()
                appointments = appt_resp.json().get("appointments", [])
            except requests.RequestException as e:
                self.stdout.write(self.style.WARNING(f"Could not fetch appointments for Dept {department_id}: {e}"))
                continue

            if not appointments:
                self.stdout.write(self.style.WARNING(f"No appointments found in Department {department_id}."))
                continue

            self.stdout.write(self.style.SUCCESS(f"Found {len(appointments)} appointments in Department {department_id}. Importing..."))
            appointments_found = True
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

                # Map provider from top-level appointment fields
                provider_id = str(appt.get("providerid") or "")
                if not provider_id:
                    continue
                
                # Use providerid as a stand-in for NPI, and create a placeholder name
                provider, _ = Provider.objects.update_or_create(
                    npi=provider_id,
                    defaults={"full_name": f"Provider {provider_id}"},
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

                # Create or update referral
                ref_date_str = appt.get("date") # API returns date as 'MM/DD/YYYY'
                if not ref_date_str:
                    continue
                
                try:
                    ref_date = datetime.strptime(ref_date_str, "%m/%d/%Y").date()
                except ValueError:
                    continue # Skip if date format is invalid

                _, created = Referral.objects.update_or_create(
                    patient=patient,
                    provider=provider,
                    referral_date=ref_date,
                    defaults={
                        "status": Referral.Status.SCHEDULED,
                        "in_network": True,  # TODO: compute real network status
                        "cost_value": 0,
                        "suggested_provider_ids": "",
                        "payer": payer,
                    },
                )
                if created:
                    created_count += 1

            self.stdout.write(self.style.SUCCESS(
                f"Imported {created_count} new referrals from Department {department_id}."
            ))
            break # Exit after finding the first department with data

        if not appointments_found:
            self.stdout.write(self.style.WARNING("Checked all departments, but no appointments were found."))
