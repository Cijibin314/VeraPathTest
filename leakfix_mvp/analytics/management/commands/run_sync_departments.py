import os
from django.core.management.base import BaseCommand
from analytics.views import _sync_departments
from analytics.models import Practice
from analytics.athena_client import get_token # Import get_token

class Command(BaseCommand):
    help = 'Runs the Athena department synchronization for a given practice.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--practice_id', 
            type=int, 
            required=True, 
            help='The local ID of the practice to sync departments for.'
        )

    def handle(self, *args, **options):
        practice_id = options['practice_id']
        
        # Get credentials from environment variables
        client_id = os.environ.get('ATHENA_CLIENT_ID')
        client_secret = os.environ.get('ATHENA_CLIENT_SECRET')

        if not client_id or not client_secret:
            self.stdout.write(self.style.ERROR(
                'Missing ATHENA_CLIENT_ID or ATHENA_CLIENT_SECRET environment variables.'
            ))
            return

        try:
            practice = Practice.objects.get(id=practice_id)
            athena_practice_id = practice.athena_practice_id
        except Practice.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f"Practice with local ID {practice_id} not found."
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Starting Athena department sync for practice: '{practice.name}' (ID: {practice_id})"
        ))

        token = get_token()
        if not token:
            self.stdout.write(self.style.ERROR("Failed to obtain Athena API token."))
            return
        
        headers = {"Authorization": f"Bearer {token}"}

        # _sync_departments is a generator, so we loop through it
        for message in _sync_departments(athena_practice_id, headers, None): # Pass None for debug_file
            self.stdout.write(message)
            
        self.stdout.write(self.style.SUCCESS("Athena department sync process finished."))
