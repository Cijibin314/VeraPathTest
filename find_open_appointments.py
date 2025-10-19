
import requests
import os
import sys
from urllib.parse import urlencode
from datetime import datetime, timedelta
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables from the .env file located in the leakfix_mvp directory
load_dotenv(dotenv_path="leakfix_mvp/.env")

# Retrieve credentials from environment variables
CLIENT_ID = os.environ.get("ATHENA_CLIENT_ID")
CLIENT_SECRET = os.environ.get("ATHENA_CLIENT_SECRET")
PRACTICE_ID = os.environ.get("ATHENA_PRACTICE_ID")

# Validate that all required environment variables are set
if not all([CLIENT_ID, CLIENT_SECRET, PRACTICE_ID]):
    print("Error: Missing required environment variables.", file=sys.stderr)
    print("Please ensure ATHENA_CLIENT_ID, ATHENA_CLIENT_SECRET, and ATHENA_PRACTICE_ID are set in your .env file.", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://api.preview.platform.athenahealth.com"
TOKEN_URL = f"{BASE_URL}/oauth2/v1/token"
API_VERSION = "v1"

def get_token():
    """
    Obtain an OAuth 2.0 token using client credentials.
    Uses Basic Authentication with Client ID and Secret.
    """
    print("Attempting to get API token...")
    try:
        response = requests.post(
            TOKEN_URL,
            auth=(CLIENT_ID, CLIENT_SECRET),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=urlencode({
                "grant_type": "client_credentials",
                "scope": "athena/service/Athenanet.MDP.*"
            })
        )
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        token = response.json().get("access_token")
        if token:
            print("Successfully obtained API token.")
            return token
        else:
            print("Error: Access token not found in response.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error getting token: {e}")
        if e.response:
            print(f"Response Body: {e.response.text}")
        return None

def api_get_request(token, endpoint, params=None):
    """
    Performs a GET request against the Athenahealth API.
    Handles both relative endpoints (e.g., '/departments') and full paths from pagination links.
    """
    # If the endpoint is a full path from a 'next' link, use it directly with the base URL
    if endpoint.startswith(f'/{API_VERSION}/'):
        url = f"{BASE_URL}{endpoint}"
        # Parameters are already included in the 'next' link, so they should be None
        params = None 
    else: # Otherwise, construct the URL from scratch
        url = f"{BASE_URL}/{API_VERSION}/{PRACTICE_ID}/{endpoint.lstrip('/')}"

    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error for URL {url}: {e}", file=sys.stderr)
        if e.response:
            print(f"Response Status: {e.response.status_code}", file=sys.stderr)
            print(f"Response Body: {e.response.text}", file=sys.stderr)
        return None

def get_all_departments(token):
    """
    Retrieves all departments for the practice, handling pagination.
    """
    print("Fetching all departments...")
    departments = []
    endpoint = "/departments"
    params = {"limit": 100} # Fetch in batches of 100

    while endpoint:
        data = api_get_request(token, endpoint, params=params if endpoint == "/departments" else None)
        if data and "departments" in data:
            departments.extend(data["departments"])
            endpoint = data.get("next") # Get the URL for the next page
            print(f"  - Fetched {len(data['departments'])} departments. Total: {len(departments)}")
        else:
            print("Could not retrieve departments or no departments found.")
            break
            
    print(f"Found a total of {len(departments)} departments.")
    return departments

def get_all_providers(token):
    """
    Retrieves all providers for the practice, handling pagination.
    """
    print("Fetching all providers...")
    providers = []
    endpoint = "/providers"
    params = {"limit": 100}

    while endpoint:
        data = api_get_request(token, endpoint, params=params if endpoint == "/providers" else None)
        if data and "providers" in data:
            providers.extend(data["providers"])
            endpoint = data.get("next")
            print(f"  - Fetched {len(data['providers'])} providers. Total: {len(providers)}")
        else:
            print("Could not retrieve providers or no providers found.")
            break
            
    print(f"Found a total of {len(providers)} providers.")
    return providers

def find_open_appointments(token):
    """
    Finds and prints all open appointment slots by checking each provider in each department.
    """
    departments = get_all_departments(token)
    if not departments:
        return

    providers = get_all_providers(token)
    if not providers:
        return

    # Define the date range for the search
    start_date = datetime.now().strftime("%m/%d/%Y")
    end_date = (datetime.now() + timedelta(days=365)).strftime("%m/%d/%Y")
    print(f"\nSearching for open appointments from {start_date} to {end_date}...\n")

    total_found = 0
    api_call_counter = 0
    total_api_calls = len(departments) * len(providers)

    for dept in departments:
        dept_id = dept.get("departmentid")
        dept_name = dept.get("name", "Unnamed Dept")
        if not dept_id:
            continue

        for prov in providers:
            api_call_counter += 1
            prov_id = prov.get("providerid")
            prov_name = prov.get("displayname", "Unnamed Prov")
            if not prov_id:
                continue

            # Display a real-time progress indicator
            progress_message = f"--> Checking {api_call_counter}/{total_api_calls} | Dept: {dept_name[:20]:<20} | Prov: {prov_name[:20]:<20}\r"
            sys.stdout.write(progress_message)
            sys.stdout.flush()

            params = {
                "departmentid": dept_id,
                "providerid": prov_id,
                "startdate": start_date,
                "enddate": end_date,
                "reasonid": 1321,  # Add the reason ID to match the creation parameter
                "limit": 200
            }
            
            data = api_get_request(token, "/appointments/open", params)
            
            if data and "appointments" in data and data["appointments"]:
                # Move to a new line to print results so the progress bar isn't overwritten
                sys.stdout.write("\n")
                appointments = data["appointments"]
                print(f"  SUCCESS: Found {len(appointments)} open slots for {prov_name} in {dept_name}:")
                for appt in appointments:
                    print(
                        f"    - Appointment ID: {appt.get('appointmentid')}, "
                        f"Date: {appt.get('date')}, "
                        f"Time: {appt.get('starttime')}"
                    )
                total_found += len(appointments)

    # Clear the progress line at the end and print final summary
    sys.stdout.write(" " * 80 + "\r")
    print(f"\nScript finished. Found a total of {total_found} open appointments.\n")


if __name__ == "__main__":
    api_token = get_token()
    if api_token:
        find_open_appointments(api_token)
