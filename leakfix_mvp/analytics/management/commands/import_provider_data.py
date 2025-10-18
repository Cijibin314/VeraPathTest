"""
Management command to import provider data from athenaOne.

This script fetches detailed information for all providers in the practice.

Usage:
    python manage.py import_provider_data --practice_id=123 \
       --client_id=YOUR_CLIENT_ID --client_secret=YOUR_SECRET
"""
import requests
from django.core.management.base import BaseCommand, CommandError
from analytics.models import Provider, Payer, Hospital
from analytics.athena_client import get_token, get

class Command(BaseCommand):
    help = "Imports provider data from athenahealth."

    def add_arguments(self, parser):
        parser.add_argument("--practice_id", required=True, help="athenaOne practice ID")

    def handle(self, *args, **opts):
        practice_id = opts["practice_id"]
        token = get_token()
        headers = {"Authorization": f"Bearer {token}"}

        try:
            provider_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/providers"
            response = requests.get(provider_url, headers=headers)
            response.raise_for_status()
            providers_data = response.json().get("providers", [])

            updated_count = 0
            for provider_summary_data in providers_data:
                provider_id = str(provider_summary_data.get("providerid"))
                if not provider_id: continue

                try:
                    # Get detailed provider data
                    self.stdout.write(f"[PROVIDER_DATA_LOG] Fetching details for provider {provider_id}")
                    provider_detail_data = get(f"providers/{provider_id}", practice_id, token, params={"showusualdepartmentguessthreshold": 0.5})
                    self.stdout.write(f"[PROVIDER_DATA_LOG]   -> Received provider detail data: {provider_detail_data}")

                    if provider_detail_data:
                        provider_detail = provider_detail_data[0]
                    else:
                        continue

                    provider = Provider.objects.get(npi=provider_id)
                    if provider_detail.get("displayname"):
                        provider.full_name = provider_detail.get("displayname")
                    else:
                        provider.full_name = f"{provider_detail.get('firstname', '')} {provider_detail.get('lastname', '')}"
                    
                    provider.specialty = provider_detail.get("specialty")
                    provider.subspecialty = provider_detail.get("specialty2")

                    # Get department and location
                    department_id = provider_detail.get("usualdepartmentid")
                    self.stdout.write(f"[PROVIDER_DATA_LOG] Provider {provider_id}: usualdepartmentid={department_id}")
                    if department_id:
                        try:
                            department_data_list = get(f"departments/{department_id}", practice_id, token)
                            if department_data_list:
                                department_data = department_data_list[0]
                                self.stdout.write(f"[PROVIDER_DATA_LOG]   -> Department data: {department_data}")
                                provider.city = department_data.get("city")
                                provider.state = department_data.get("state")
                                provider.primary_department = department_data.get("name")
                                self.stdout.write(f"[PROVIDER_DATA_LOG]   -> Setting city={provider.city}, state={provider.state}, primary_department={provider.primary_department}")

                                if department_data.get("ishospitaldepartment"):
                                    hospital, _ = Hospital.objects.get_or_create(name=department_data.get("name"))
                                    provider.hospital_affiliations.add(hospital)
                        except requests.RequestException as e:
                            self.stdout.write(self.style.WARNING(f"\n  -> API error for department {department_id}: {e}. Skipping location data."))

                    provider.accepting_new_patients = provider_detail.get("acceptingnewpatients")

                    provider.save()
                    updated_count += 1
                except Provider.DoesNotExist:
                    # This provider is not in our system, so we don't need to do anything.
                    pass
                except requests.RequestException as e:
                    self.stdout.write(self.style.WARNING(f"\n  -> API error for provider {provider_id}: {e}. Skipping provider."))


            self.stdout.write(self.style.SUCCESS(f"Successfully updated {updated_count} providers."))

        except requests.RequestException as e:
            raise CommandError(f"Failed to fetch providers: {e}")
