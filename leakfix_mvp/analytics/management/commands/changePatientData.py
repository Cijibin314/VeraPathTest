from django.core.management.base import BaseCommand
from leakfix_mvp.analytics.models import Referral, Patient, Provider, Invoice, Metric, ReferralHistory, Payer, ImportLog
import hashlib

class Command(BaseCommand):
    help = 'Clears the database of all data except for practices and users.'

    def handle(self, *args, **options):
        self.stdout.write('Starting...')
        num = 60183
        pseudonym_for_lookup = hashlib.sha256(str(num).encode()).hexdigest()

        Patient.objects.update_or_create(
            pseudonym=pseudonym_for_lookup,
            defaults={
                "original_id": 60183,
                "first_name": "Gary",
                "last_name": "Sandboxtest",
            }
        )
        self.stdout.write(self.style.SUCCESS('Success'))
