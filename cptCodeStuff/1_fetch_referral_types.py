import os
import requests
import string
import itertools
import time
import argparse
import logging
from urllib.parse import urlencode
import csv

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Athena API Configuration ---
# CLIENT_ID and CLIENT_SECRET will now be passed as command-line arguments.
TOKEN_URL = "https://api.preview.platform.athenahealth.com/oauth2/v1/token"
BASE_URL = "https://api.preview.platform.athenahealth.com"


def get_token(client_id, client_secret):
    """Obtains an OAuth2 token from Athena using provided client ID and secret."""
    token = None
    try:
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "athena/service/Athenanet.MDP.*"
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        r = requests.post(TOKEN_URL, data=urlencode(data), headers=headers)
        r.raise_for_status()
        token_data = r.json()
        token = token_data.get("access_token")
        logging.info("Successfully obtained API token.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting token: {e}")
        if e.response:
            logging.error(f"Response Body: {e.response.text}")
    return token

def fetch_referral_order_types(practice_id, token, search_value):
    """Fetches referral order types for a given search value."""
    endpoint = f"/v1/{practice_id}/reference/order/referral"
    url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"searchvalue": search_value}

    try:
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logging.info(f"API returned 404 (Not Found) for search value: '{search_value}'")
        else:
            logging.error(f"API Error for search '{search_value}': {e}")
            logging.error(f"Response Body: {e.response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error for search '{search_value}': {e}")
    return None

def main():
    """
    Main function to fetch all referral order types.
    """
    parser = argparse.ArgumentParser(description="Fetch all referral order types from the Athena API.")
    parser.add_argument("practiceid", type=str, help="The Athena practice ID.")
    parser.add_argument("--client_id", type=str, required=True, help="Your Athena API Client ID.")
    parser.add_argument("--client_secret", type=str, required=True, help="Your Athena API Client Secret.")
    parser.add_argument("--output_file", type=str, default="referral_order_types.csv",
                        help="The CSV file to save the unique referral order types to.")
    args = parser.parse_args()

    token = get_token(args.client_id, args.client_secret)
    if not token:
        logging.error("Could not retrieve API token. Exiting.")
        return

    unique_order_types = set()
    chars = string.ascii_lowercase
    search_combinations = itertools.product(chars, repeat=2)
    total_combinations = len(chars) ** 2
    logging.info(f"Starting fetch... There are {total_combinations} search combinations.")

    for i, combo in enumerate(search_combinations):
        search_term = "".join(combo)
        logging.info(f"Processing combination {i+1}/{total_combinations}: '{search_term}'")

        data = fetch_referral_order_types(args.practiceid, token, search_term)

        if data and isinstance(data, list): 
            for order_type in data:
                ordertypeid = order_type.get("ordertypeid")
                name = order_type.get("name")
                if ordertypeid and name:
                    unique_order_types.add((str(ordertypeid), name))
        
        logging.info(f"Unique order types found so far: {len(unique_order_types)}")
        time.sleep(0.1)

    logging.info(f"--- Fetch Complete ---")
    logging.info(f"Found {len(unique_order_types)} unique referral order types.")

    # --- Part 2: Save to CSV ---
    output_filepath = args.output_file
    try:
        with open(output_filepath, 'w', newline='') as csvfile:
            fieldnames = ['ordertypeid', 'name']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for ordertypeid, name in sorted(list(unique_order_types)):
                writer.writerow({'ordertypeid': ordertypeid, 'name': name})
        logging.info(f"Successfully saved {len(unique_order_types)} referral order types to '{output_filepath}'")
    except IOError as e:
        logging.error(f"Error writing to file '{output_filepath}': {e}")


if __name__ == "__main__":
    main()