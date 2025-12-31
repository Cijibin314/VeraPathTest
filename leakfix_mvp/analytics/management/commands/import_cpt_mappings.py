import csv
from django.core.management.base import BaseCommand, CommandError
from leakfix_mvp.analytics.models import CPTCodeMapping

class Command(BaseCommand):
    help = 'Imports CPT code mappings from a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file to import.')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']

        try:
            with open(csv_file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        mapping, created = CPTCodeMapping.objects.update_or_create(
                            referral_order_id=row['referral_order_id'],
                            defaults={
                                'referral_order_name': row['referral_order_name'],
                                'cpt_code': row['cpt_code'],
                                'notes': row.get('notes', ''),
                            }
                        )
                        if created:
                            self.stdout.write(self.style.SUCCESS(f"Created mapping for {row['referral_order_name']}"))
                        else:
                            self.stdout.write(self.style.SUCCESS(f"Updated mapping for {row['referral_order_name']}"))
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"Error processing row: {row}. Error: {e}"))
        except FileNotFoundError:
            raise CommandError(f'File "{csv_file_path}" does not exist.')

        self.stdout.write(self.style.SUCCESS('Successfully imported CPT code mappings.'))
