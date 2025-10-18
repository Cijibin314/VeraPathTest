"""
Management command to mark preferred providers based on ACO rules.
"""
import json
from django.core.management.base import BaseCommand
from analytics.models import Provider

class Command(BaseCommand):
    help = "Marks preferred providers based on ACO rules."

    def handle(self, *args, **options):
        with open('ACO.txt') as f:
            aco_data = json.load(f)

        in_network_providers = aco_data.get("in-network_providers", [])
        location = aco_data.get("location")
        preferred_payers = aco_data.get("preferred_payers", [])

        providers = Provider.objects.all()

        for provider in providers:
            provider.is_preferred = False

            if provider.full_name in in_network_providers:
                provider.is_preferred = True

            if location and provider.city and provider.state:
                if f"{provider.city}, {provider.state}" in location:
                    provider.is_preferred = True

            for payer in provider.insurances_accepted.all():
                if payer.name in preferred_payers:
                    provider.is_preferred = True
                    break

        self.stdout.write(self.style.SUCCESS("Successfully marked preferred providers."))
