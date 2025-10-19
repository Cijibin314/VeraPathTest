
import requests
import os
import sys
import argparse
from urllib.parse import urlencode
from datetime import datetime
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables from the .env file located in the leakfix_mvp directory
dotenv_path = os.path.join(os.path.dirname(__file__), 'leakfix_mvp', '.env')
load_dotenv(dotenv_path=dotenv_path)

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
        response.raise_for_status()
        token = response.json().get("access_token")
        if token:
            print("Successfully obtained API token.")
            return token
        else:
            print("Error: Access token not found in response.", file=sys.stderr)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error getting token: {e}", file=sys.stderr)
        if e.response:
            print(f"Response Body: {e.response.text}", file=sys.stderr)
        return None

def create_open_appointment_slot(token, provider_id, department_id, appt_date, appt_times, reason_id):
    """
    Creates one or more new open appointment slots for a given day.
    """
    endpoint = f"/{API_VERSION}/{PRACTICE_ID}/appointments/open"
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # The payload needs to handle multiple values for the 'appointmenttime' key.
    # We create a list of tuples to be encoded.
    payload = [
        ("providerid", provider_id),
        ("departmentid", department_id),
        ("appointmentdate", appt_date),
        ("reasonid", reason_id),
    ]
    for time in appt_times:
        payload.append(("appointmenttime", time))

    # urlencode with doseq=True correctly formats the list of times
    encoded_payload = urlencode(payload, doseq=True)

    print(f"\nAttempting to create open slot(s) for provider {provider_id} in department {department_id} on {appt_date} at {', '.join(appt_times)}...")

    try:
        response = requests.post(url, headers=headers, data=encoded_payload)
        response.raise_for_status()
        
        response_data = response.json()
        if response_data.get("success") and response_data.get("appointmentids"):
            print(f"Successfully created appointment slots!")
            print(f"New Appointment IDs: {response_data['appointmentids']}")
        else:
            print("Request was successful but response indicates failure or no IDs returned.")
            print(f"Response: {response_data}")

    except requests.exceptions.RequestException as e:
        print(f"API Error creating appointment slot: {e}", file=sys.stderr)
        if e.response:
            print(f"Response Status: {e.response.status_code}", file=sys.stderr)
            print(f"Response Body: {e.response.text}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Create open appointment slots in the Athenahealth sandbox.")
    parser.add_argument("--providerid", type=int, required=True, help="The athenaNet provider ID.")
    parser.add_argument("--departmentid", type=int, required=True, help="The athenaNet department ID.")
    parser.add_argument("--date", type=str, required=True, help="The date for the new slot (format: MM/DD/YYYY).")
    parser.add_argument("--time", type=str, action='append', required=True, help="The time for the new slot (format: HH:MM). Can be specified multiple times.")
    parser.add_argument("--reasonid", type=int, default=1321, help="The appointment reason ID. Defaults to 1321.")

    args = parser.parse_args()

    # Validate date and time formats
    try:
        datetime.strptime(args.date, "%m/%d/%Y")
    except ValueError:
        print(f"Error: Invalid date format for --date. Please use MM/DD/YYYY.", file=sys.stderr)
        sys.exit(1)
    for t in args.time:
        try:
            datetime.strptime(t, "%H:%M")
        except ValueError:
            print(f"Error: Invalid time format for --time: '{t}'. Please use HH:MM.", file=sys.stderr)
            sys.exit(1)

    api_token = get_token()
    if api_token:
        create_open_appointment_slot(
            token=api_token,
            provider_id=args.providerid,
            department_id=args.departmentid,
            appt_date=args.date,
            appt_times=args.time,
            reason_id=args.reasonid
        )

if __name__ == "__main__":
    main()
