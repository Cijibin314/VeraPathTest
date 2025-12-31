from django.core.management.base import BaseCommand
from leakfix_mvp.analytics.models import Referral, Patient, Provider, Invoice, Metric, ReferralHistory, Payer, ImportLog
import hashlib

class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write('Starting...')
        num = 71
        pseudonym_for_lookup = hashlib.sha256(str(num).encode()).hexdigest()

        provider = Provider.objects.get(pseudonym=pseudonym_for_lookup)
        self.stdout.write(provider)
        self.stdout.write(self.style.SUCCESS('Success'))
