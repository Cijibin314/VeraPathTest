from django.core.management.base import BaseCommand
from leakfix_mvp.analytics.models import Patient

class Command(BaseCommand):
    help = 'Lists all patients in the database with their IDs and names.'

    def handle(self, *args, **options):
        patients = Patient.objects.all()
        if not patients:
            self.stdout.write(self.style.WARNING('No patients found in the database.'))
            return

        self.stdout.write(self.style.SUCCESS('Listing all patients:'))
        for patient in patients:
            if(patient.original_id != '60178'):
                continue
            self.stdout.write(
                f"ID: {patient.pk}, "
                f"Original ID: '{patient.original_id}', "
                f"Pseudonym: '{patient.pseudonym}', "
                f"First Name: '{patient.first_name}', "
                f"Last Name: '{patient.last_name}'"
            )
