import os
from django.core.management.base import BaseCommand
from django.conf import settings
from analytics.views import run_full_athena_sync
from analytics.models import Practice

class Command(BaseCommand):
    help = 'Runs the full Athena data synchronization for a given practice.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--practice_id', 
            type=int, 
            required=True, 
            help='The local ID of the practice to sync.'
        )

    def handle(self, *args, **options):
        practice_id = options['practice_id']
        
        # Get credentials from environment variables
        # These are the same variables used by the web application
        client_id = os.environ.get('ATHENA_CLIENT_ID')
        client_secret = os.environ.get('ATHENA_CLIENT_SECRET')

        if not client_id or not client_secret:
            self.stdout.write(self.style.ERROR(
                'Missing ATHENA_CLIENT_ID or ATHENA_CLIENT_SECRET environment variables.'
            ))
            return

        try:
            practice = Practice.objects.get(id=practice_id)
            self.stdout.write(self.style.SUCCESS(
                f"Starting full Athena sync for practice: '{practice.name}' (ID: {practice_id})"
            ))
        except Practice.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f"Practice with local ID {practice_id} not found."
            ))
            return

        # The run_full_athena_sync function from views.py is a generator.
        # We loop through it and print each message it yields.
        for message in run_full_athena_sync(practice_id, client_id, client_secret):
            self.stdout.write(message)
            
        self.stdout.write(self.style.SUCCESS("Athena sync process finished."))
