from django.core.management.base import BaseCommand, CommandError
import requests
from analytics.athena_client import get_token

class Command(BaseCommand):
    help = "Finds a valid provider-department pair for creating encounters (ordergroups)."

    def add_arguments(self, parser):
        parser.add_argument("practice_id", type=str, help="Athenahealth practice ID")
        parser.add_argument("patient_id", type=str, help="A test patient ID to use for the check.")
        parser.add_argument("--client_id", required=True, help="AthenaOne API client ID")
        parser.add_argument("--client_secret", required=True, help="AthenaOne API client secret")

    def handle(self, *args, **options):
        practice_id = options["practice_id"]
        patient_id = options["patient_id"]
        client_id = options["client_id"]
        client_secret = options["client_secret"]

        self.stdout.write("Attempting to find a valid provider-department pair...")

        token = get_token()
        if not token:
            raise CommandError("Could not get an Athena API token.")

        headers = {"Authorization": f"Bearer {token}"}

        # Get all providers
        try:
            providers_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/providers"
            response = requests.get(providers_url, headers=headers)
            response.raise_for_status()
            providers = response.json().get("providers", [])
            self.stdout.write(f"Found {len(providers)} providers.")
        except requests.RequestException as e:
            raise CommandError(f"Failed to fetch providers: {e}")

        # Get all departments
        try:
            departments_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/departments"
            response = requests.get(departments_url, headers=headers)
            response.raise_for_status()
            departments = response.json().get("departments", [])
            self.stdout.write(f"Found {len(departments)} departments.")
        except requests.RequestException as e:
            raise CommandError(f"Failed to fetch departments: {e}")

        # Loop and test
        for provider in providers:
            provider_id = provider.get("providerid")
            if not provider_id:
                continue

            for department in departments:
                department_id = department.get("departmentid")
                if not department_id:
                    continue

                self.stdout.write(f"Testing provider {provider_id} with department {department_id}...")
                
                try:
                    ordergroup_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/chart/{patient_id}/ordergroups"
                    payload = {
                        'patientid': patient_id,
                        'departmentid': department_id,
                        'orderingproviderid': provider_id
                    }
                    response = requests.post(ordergroup_url, headers=headers, data=payload)
                    response.raise_for_status()
                    
                    # If we reach here, it means the call was successful
                    self.stdout.write(self.style.SUCCESS(f"\n\nSUCCESS! Found a valid combination:"))
                    self.stdout.write(self.style.SUCCESS(f"  Provider ID: {provider_id} ({provider.get('displayname')})"))
                    self.stdout.write(self.style.SUCCESS(f"  Department ID: {department_id} ({department.get('name')})"))
                    self.stdout.write(self.style.SUCCESS(f"You can now use this combination to create encounters."))
                    return # Exit after finding the first valid pair

                except requests.exceptions.HTTPError as e:
                    error_text = e.response.text
                    if e.response.status_code == 400 or e.response.status_code == 404:
                        #self.stdout.write(f"Error text: {error_text}")
                        if "does not have access to or cannot be a rendering provider" in error_text:
                            pass # Suppress this expected error
                        elif "The specified patient does not exist in that department" in error_text:
                            pass # Suppress this expected error
                        else:
                            self.stdout.write(self.style.WARNING(f"  -> Unexpected 400 error: {error_text}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"  -> Unexpected error: {e.response.status_code} {error_text}"))
        
        self.stdout.write(self.style.ERROR("Could not find any provider-department combination."))
