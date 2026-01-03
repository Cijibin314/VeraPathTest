import os
from django.core.management.base import BaseCommand
from django.conf import settings
from analytics.views import run_full_athena_sync
from analytics.models import Practice

class Command(BaseCommand):
    help = 'Runs the full Athena data synchronization for a given practice.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--athena_id', 
            type=str, 
            required=True, 
            help='The Athena Practice ID of the practice to sync.'
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
            self.stdout.write(self.style.SUCCESS(
                f"Starting full Athena sync for practice: '{practice.name}' (Athena ID: {athena_id})"
            ))
        except Practice.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f"Practice with Athena ID {athena_id} not found in the database."
            ))
            return

        # The underlying sync function expects the local database ID (pk), so we pass practice.id
        for message in run_full_athena_sync(practice.id, client_id, client_secret):
            self.stdout.write(message)
            
        self.stdout.write(self.style.SUCCESS("Athena sync process finished."))