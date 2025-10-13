"""
Management command to import referral data from a CSV.

The CSV should have headers matching the following columns (case‑insensitive):

  - patient_id: Unique identifier from the source EHR.  Will be hashed.
  - npi: Provider's National Provider Identifier.
  - payer_code: Insurance plan code.  A new `Payer` will be created if not found.
  - in_network: Boolean (True/False or 1/0).
  - cost_value: Decimal amount representing revenue or reimbursement value.
  - status: One of the referral statuses (pending, sent, ack, scheduled,
            completed, cancelled).  Defaults to 'pending' if not provided.

Example usage:

    python manage.py import_referrals path/to/referrals.csv

This command will create or update `Provider`, `Patient`, and `Payer` entries
as needed, then insert `Referral` records.
"""
import csv
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from analytics.models import Provider, Patient, Payer, Referral

class Command(BaseCommand):
    help = 'Import referrals from a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', help='Path to the referrals CSV file')

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        try:
            with open(csv_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                required = {'patient_id', 'npi', 'payer_code', 'in_network', 'cost_value'}
                missing = required - {h.lower() for h in reader.fieldnames}
                if missing:
                    raise CommandError(f"CSV is missing required headers: {', '.join(missing)}")

                count = 0
                for row in reader:
                    patient_id = row.get('patient_id') or row.get('patientID') or row.get('patient')
                    npi = row.get('npi')
                    payer_code = row.get('payer_code') or row.get('payer')
                    in_network = str(row.get('in_network')).strip().lower() in ('1', 'true', 'yes')
                    cost_value = Decimal(row.get('cost_value') or '0')
                    status = row.get('status', Referral.Status.PENDING).lower()

                    # Get or create patient
                    patient, _ = Patient.objects.get_or_create(original_id=patient_id)
                    # Get or create provider
                    provider, _ = Provider.objects.get_or_create(
                        npi=npi,
                        defaults={'full_name': f'Provider {npi}', 'specialty': '', 'subspecialty': '', 'city': '', 'state': ''}
                    )
                    # Get or create payer
                    payer = None
                    if payer_code:
                        payer, _ = Payer.objects.get_or_create(code=payer_code, defaults={'name': payer_code})

                    Referral.objects.create(
                        patient=patient,
                        provider=provider,
                        payer=payer,
                        status=status,
                        in_network=in_network,
                        cost_value=cost_value,
                    )
                    count += 1

                self.stdout.write(self.style.SUCCESS(f'Imported {count} referral records.'))
        except FileNotFoundError:
            raise CommandError(f"File not found: {csv_path}")
