
import os
import requests
import json
from datetime import datetime, timedelta

# --- Configuration ---
# Credentials should be set as environment variables
CLIENT_ID = os.environ.get("ATHENA_CLIENT_ID")
CLIENT_SECRET = os.environ.get("ATHENA_CLIENT_SECRET")

# API details from our successful tests
TOKEN_URL = "https://api.preview.platform.athenahealth.com/oauth2/v1/token"
API_BASE_URL = "https://api.preview.platform.athenahealth.com"
PRACTICE_ID = "195900"
SCOPE = "system/CarePlan.read"

def get_token(scope):
    """Obtain an OAuth 2.0 token using client credentials."""
    print(f"Requesting token with scope: {scope}...")
    payload = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': scope
    }
    try:
        response = requests.post(TOKEN_URL, data=payload)
        response.raise_for_status()
        token = response.json()['access_token']
        print("Successfully obtained token.")
        return token
    except requests.exceptions.HTTPError as e:
        print(f"Error getting token: {e.response.status_code} - {e.response.text}")
        raise

def get_department_id(token, practice_id):
    """Fetch the first department ID for a given practice."""
    print(f"\nFetching departments for practice '{practice_id}'...")
    url = f"{API_BASE_URL}/v1/{practice_id}/departments"
    headers = {'Authorization': f'Bearer {token}'}
    params = {'limit': 1}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        department_id = data['departments'][0]['departmentid']
        print(f"Successfully found department ID: {department_id}")
        return department_id
    except (requests.exceptions.HTTPError, KeyError, IndexError) as e:
        print(f"Error fetching department ID: {e}")
        if 'response' in locals():
            print(f"Response: {response.text}")
        raise

def get_appointments(token, practice_id, department_id):
    """Fetch appointments for a given practice and department."""
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\nFetching appointments for practice '{practice_id}', department '{department_id}'...")
    print(f"Date range: {start_date} to {end_date}")

    url = f"{API_BASE_URL}/v1/{practice_id}/appointments"
    headers = {'Authorization': f'Bearer {token}'}
    params = {
        'departmentid': department_id,
        'startdate': start_date,
        'enddate': end_date,
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        print("Successfully fetched appointments.")
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"Error fetching appointments: {e.response.status_code} - {e.response.text}")
        raise

def main():
    """Main function to execute the API client flow."""
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: ATHENA_CLIENT_ID and ATHENA_CLIENT_SECRET environment variables must be set.")
        return

    try:
        # Step 1: Get the token
        access_token = get_token(SCOPE)
        
        # Step 2: Get a department ID
        department_id = get_department_id(access_token, PRACTICE_ID)

        # Step 3: Get appointments using the department ID
        appointments_data = get_appointments(access_token, PRACTICE_ID, department_id)
        
        # Step 4: Print the results
        print("\n--- API Response ---")
        print(json.dumps(appointments_data, indent=2))
        print(f"\nTotal appointments found: {appointments_data.get('totalcount')}")

    except Exception as e:
        print(f"\nAn error occurred during the API flow: {e}")

if __name__ == "__main__":
    main()
