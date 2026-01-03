import os
from django.core.management.base import BaseCommand
from analytics.views import _sync_patients
from analytics.models import Practice
from analytics.athena_client import get_token

class Command(BaseCommand):
    help = 'Runs the Athena patient synchronization for a given practice.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--athena_id', 
            type=str, 
            required=True, 
            help='The Athena Practice ID of the practice to sync patients for.'
        )

    def handle(self, *args, **options):
        athena_id = options['athena_id']
        
        # Get credentials from environment variables
        client_id = os.environ.get('ATHENA_CLIENT_ID')
        client_secret = os.environ.get('ATHENA_CLIENT_SECRET')

        if not client_id or not client_secret:
            self.stdout.write(self.style.ERROR(
                'Missing ATHENA_CLIENT_ID or ATHENA_CLIENT_SECRET environment variables.'
            ))
            return

        try:
            practice = Practice.objects.get(athena_practice_id=athena_id)
        except Practice.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f"Practice with Athena ID {athena_id} not found in the database."
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Starting Athena patient sync for practice: '{practice.name}' (Athena ID: {athena_id})"
        ))

        token = get_token()
        if not token:
            self.stdout.write(self.style.ERROR("Failed to obtain Athena API token."))
            return
        
        # The underlying sync function expects the Athena Practice ID and token
        for message in _sync_patients(athena_id, token, None): # Pass None for debug_file
            self.stdout.write(message)
            
        self.stdout.write(self.style.SUCCESS("Athena patient sync process finished."))