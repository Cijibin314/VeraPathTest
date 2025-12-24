from django.core.management.base import BaseCommand
from analytics.models import Referral, Patient, Provider, Invoice, Metric, ReferralHistory, Payer, ImportLog

class Command(BaseCommand):
    help = 'Clears the database of all data except for practices and users.'

    def handle(self, *args, **options):
        self.stdout.write('Clearing database...')

        # The order of deletion matters to avoid foreign key constraint issues.
        # Start with models that have foreign keys to other models.


        # ReferralHistory.objects.all().delete()
        # self.stdout.write(self.style.SUCCESS('Successfully deleted all ReferralHistory objects.'))
        
        # Referral.objects.all().delete()
        # self.stdout.write(self.style.SUCCESS('Successfully deleted all Referral objects.'))

        # Patient.objects.all().delete()
        # self.stdout.write(self.style.SUCCESS('Successfully deleted all Patient objects.'))

        Provider.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted all Provider objects.'))

        # Invoice.objects.all().delete()
        # self.stdout.write(self.style.SUCCESS('Successfully deleted all Invoice objects.'))

        # Metric.objects.all().delete()
        # self.stdout.write(self.style.SUCCESS('Successfully deleted all Metric objects.'))

        # Payer.objects.all().delete()
        # self.stdout.write(self.style.SUCCESS('Successfully deleted all Payer objects.'))

        # ImportLog.objects.all().delete()
        # self.stdout.write(self.style.SUCCESS('Successfully deleted all ImportLog objects.'))

        self.stdout.write(self.style.SUCCESS('Database cleared successfully.'))
