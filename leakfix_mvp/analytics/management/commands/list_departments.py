from django.core.management.base import BaseCommand, CommandError
from leakfix_mvp.analytics.models import Practice
from leakfix_mvp.analytics.athena_client import get_token, get
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fetches and lists all departments for a given practice from Athena.'

    def add_arguments(self, parser):
        parser.add_argument('athena_practice_id', type=str, help='The Athena ID of the practice to query departments for.')

    def handle(self, *args, **options):
        athena_practice_id = options['athena_practice_id']
        
        try:
            practice = Practice.objects.get(athena_practice_id=athena_practice_id)
            self.stdout.write(self.style.SUCCESS(f"Fetching departments for practice '{practice.name}' (Athena ID: {athena_practice_id})..."))
        except Practice.DoesNotExist:
            raise CommandError(f'Practice with Athena ID "{athena_practice_id}" does not exist.')

        token = get_token()
        if not token:
            raise CommandError('Failed to obtain Athena API token. Check client ID/secret settings.')

        try:
            departments_data = get("departments", athena_practice_id, token, params={"limit": 1000})
            
            if not departments_data or not departments_data.get("departments"):
                self.stdout.write(self.style.WARNING(f"No departments found for practice '{practice.name}'."))
                return

            self.stdout.write(self.style.SUCCESS(f"\nListing departments for practice '{practice.name}':"))
            for dept in departments_data["departments"]:
                self.stdout.write(
                    f"  ID: {dept.get('departmentid')}, Name: '{dept.get('name')}', "
                    f"Address: '{dept.get('address1', '')}, {dept.get('city', '')}, {dept.get('state', '')}'"
                )
            self.stdout.write(self.style.SUCCESS(f"\nFound {len(departments_data['departments'])} departments."))

        except Exception as e:
            logger.error(f"Error fetching departments from Athena: {e}", exc_info=True)
            raise CommandError(f"Error fetching departments from Athena: {e}")
