"""
Management command to import provider data from athenaOne.

This script fetches detailed information for all providers in the practice.

Usage:
    python manage.py import_provider_data --practice_id=123 \
       --client_id=YOUR_CLIENT_ID --client_secret=YOUR_SECRET
"""
import requests
from django.core.management.base import BaseCommand, CommandError
from analytics.models import Provider
from analytics.athena_client import get_token

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
            for provider_data in providers_data:
                provider_id = str(provider_data.get("providerid"))
                if not provider_id: continue

                try:
                    provider = Provider.objects.get(npi=provider_id)
                    if provider_data.get("displayname"):
                        provider.full_name = provider_data.get("displayname")
                    if provider_data.get("specialty"):
                        provider.specialty = provider_data.get("specialty")
                    provider.subspecialty = provider_data.get("specialty2")
                    provider.city = provider_data.get("city")
                    provider.state = provider_data.get("state")
                    provider.save()
                    updated_count += 1
                except Provider.DoesNotExist:
                    # This provider is not in our system, so we don't need to do anything.
                    pass

            self.stdout.write(self.style.SUCCESS(f"Successfully updated {updated_count} providers."))

        except requests.RequestException as e:
            raise CommandError(f"Failed to fetch providers: {e}")
