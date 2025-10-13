"""
Import data from a FHIR server (stub).

This management command outlines how to connect to a FHIR server (e.g. Epic’s
FHIR API), authenticate, fetch patient and referral resources, and save them
into the local database.  Because this environment has no external network,
the command only prints instructions.  Use it as a template once you have
FHIR API credentials.
"""
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Import referral and patient data from a FHIR API (placeholder).'

    def add_arguments(self, parser):
        parser.add_argument('--base_url', type=str, help='FHIR base URL')
        parser.add_argument('--client_id', type=str, help='Client ID')
        parser.add_argument('--client_secret', type=str, help='Client secret')
        parser.add_argument('--identifier_system', type=str, help='Patient identifier system (e.g. MRN system)')

    def handle(self, *args, **opts):
        if not (opts.get('base_url') and opts.get('client_id') and opts.get('client_secret')):
            raise CommandError('You must provide base_url, client_id, and client_secret.')
        self.stdout.write(self.style.WARNING('This is a stub for FHIR import.'))
        self.stdout.write(self.style.WARNING('Implement OAuth2, fetch Patient and ServiceRequest resources,'))
        self.stdout.write(self.style.WARNING('and map them to Patient, Provider, and Referral models.'))
        self.stdout.write(self.style.SUCCESS('FHIR import completed (no data imported in stub).'))
