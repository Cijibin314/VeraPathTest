
"""
Utility script to fetch and display details for a specific provider from the Athenahealth API.

This helps in debugging by allowing you to inspect a provider's data, such as their
associated departments, to find valid combinations for other API calls.

Usage:
    python get_provider_details.py <provider_id>
"""

import requests
import os
import sys
import argparse
import json
from urllib.parse import urlencode
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables from the .env file located in the leakfix_mvp directory
dotenv_path = os.path.join(os.path.dirname(__file__), 'leakfix_mvp', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Retrieve credentials from environment variables
CLIENT_ID = os.environ.get("ATHENA_CLIENT_ID")
CLIENT_SECRET = os.environ.get("ATHENA_CLIENT_SECRET")
PRACTICE_ID = os.environ.get("ATHENA_PRACTICE_ID")

BASE_URL = "https://api.preview.platform.athenahealth.com"
TOKEN_URL = f"{BASE_URL}/oauth2/v1/token"
API_VERSION = "v1"

def get_token():
    """Obtain an OAuth 2.0 token using client credentials."""
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

def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Fetch details for a specific provider.")
    parser.add_argument("providerid", type=int, help="The athenaNet provider ID to look up.")
    args = parser.parse_args()

    # --- Validation ---
    if not all([CLIENT_ID, CLIENT_SECRET, PRACTICE_ID]):
        print("Error: Missing required environment variables.", file=sys.stderr)
        print("Please ensure ATHENA_CLIENT_ID, ATHENA_CLIENT_SECRET, and ATHENA_PRACTICE_ID are set.", file=sys.stderr)
        sys.exit(1)

    # --- Main Logic ---
    api_token = get_token()
    if not api_token:
        sys.exit(1)

    print(f"\nFetching details for provider ID: {args.providerid}...")

    endpoint = f"/{API_VERSION}/{PRACTICE_ID}/providers/{args.providerid}"
    url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {api_token}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        provider_details = response.json()

        print("\n--- Provider Details ---")
        # Print the JSON response in a readable format
        print(json.dumps(provider_details, indent=2))
        print("------------------------\n")

        # Helpful summary
        if provider_details and isinstance(provider_details, list):
            provider = provider_details[0]
            print("Summary:")
            print(f"  Display Name: {provider.get('displayname')}")
            print(f"  Specialty: {provider.get('specialty')}")
            print(f"  Department List: {provider.get('departmentlist')}")

    except requests.exceptions.RequestException as e:
        print(f"API Error fetching provider details: {e}", file=sys.stderr)
        if e.response:
            print(f"Response Status: {e.response.status_code}", file=sys.stderr)
            print(f"Response Body: {e.response.text}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
