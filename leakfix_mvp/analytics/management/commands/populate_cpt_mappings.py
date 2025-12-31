
import csv
import logging
import argparse
import re
import string
import itertools
import time
import requests
from urllib.parse import urlencode

from django.core.management.base import BaseCommand, CommandError
from leakfix_mvp.analytics.models import CPTCodeMapping

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Athena API Configuration ---
TOKEN_URL = "https://api.preview.platform.athenahealth.com/oauth2/v1/token"
BASE_URL = "https://api.preview.platform.athenahealth.com"


def parse_master_cpt_file(filepath: str) -> set:
    """Parses the provided text file to extract a set of valid CPT/HCPCS codes."""
    valid_codes = set()
    code_pattern = re.compile(r'^[0-9A-Z]{5}\s')  # Matches a 5-character alphanumeric code at the start of a line
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                match = code_pattern.match(line)
                if match:
                    valid_codes.add(match.group().strip())
        logging.info(f"Successfully parsed {len(valid_codes)} unique codes from '{filepath}'.")
        return valid_codes
    except FileNotFoundError:
        logging.error(f"Master CPT code file not found at: {filepath}")
        raise
    except Exception as e:
        logging.error(f"Error reading master CPT code file: {e}")
        raise

def get_token(client_id, client_secret):
    """Obtains an OAuth2 token from Athena."""
    # (Implementation is the same as in the previous script)
    token = None
    try:
        r = requests.post(TOKEN_URL, data=urlencode({
            "grant_type": "client_credentials", "client_id": client_id,
            "client_secret": client_secret, "scope": "athena/service/Athenanet.MDP.*"
        }), headers={"Content-Type": "application/x-www-form-urlencoded"})
        r.raise_for_status()
        token = r.json().get("access_token")
        logging.info("Successfully obtained API token.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting token: {e}")
        if e.response: logging.error(f"Response Body: {e.response.text}")
    return token

def fetch_all_referral_order_types(practice_id, token) -> set:
    """Fetches all referral order types by iterating through search terms."""
    unique_order_types = set()
    chars = string.ascii_lowercase
    search_combinations = [''.join(c) for c in itertools.product(chars, repeat=2)]
    
    logging.info(f"Starting fetch of referral order types from Athena...")
    for i, search_term in enumerate(search_combinations):
        logging.info(f"Processing combination {i+1}/{len(search_combinations)}: '{search_term}'")
        try:
            url = f"{BASE_URL}/v1/{practice_id}/reference/order/referral"
            headers = {"Authorization": f"Bearer {token}"}
            params = {"searchvalue": search_term}
            r = requests.get(url, headers=headers, params=params)
            if r.status_code == 404:
                continue
            r.raise_for_status()
            data = r.json()
            if data and isinstance(data, list):
                for order_type in data:
                    if order_type.get("ordertypeid") and order_type.get("name"):
                        unique_order_types.add((str(order_type["ordertypeid"]), order_type["name"]))
        except requests.exceptions.RequestException as e:
            logging.error(f"API error for search '{search_term}': {e}")
        time.sleep(0.1) # Be respectful to the API server
        
    logging.info(f"Found {len(unique_order_types)} unique referral order types.")
    return unique_order_types

def guess_cpt_code(name: str) -> str:
    """Guesses a CPT code or range based on the referral name."""
    # (Implementation is the same as in generate_cpt_codes.py)
    name = name.lower()
    if "consultation" in name: return "99241-99245"
    if "physical therap" in name: return "97110"
    if "chiropractor" in name: return "98940-98942"
    if "psychiatrist" in name or "psychotherapy" in name or "psychologist" in name or "mental health" in name: return "90832-90838"
    if "cardio" in name or "heart" in name: return "93000-93272"
    if "dermatologist" in name: return "99202-99215"
    if "ophthalmologist" in name or "eye care" in name: return "92002-92014"
    if "radio" in name or "imaging" in name: return "70010-79999"
    if "surg" in name: return "10021-69990"
    if "orthopedic" in name: return "20100-29999"
    if "neurologist" in name or "neuro" in name: return "95812-95913"
    if "gastroenterologist" in name: return "91000-91299"
    if "oncologist" in name or "cancer" in name: return "96401-96549"
    if "otolaryngologist" in name or "ent" in name: return "92502-92700"
    if "urologist" in name: return "50010-53899"
    if "pulmonary" in name or "lung" in name: return "94010-94799"
    if "endocrinology" in name or "diabetes" in name: return "95249-95251"
    if "nephrologist" in name or "kidney" in name or "ckd" in name: return "90935-90999"
    if "podiatrist" in name or "foot" in name: return "28001-28899"
    if "nutritionist" in name or "dietitian" in name: return "97802-97804"
    if "home health" in name: return "99500-99602"
    if "genetics" in name: return "81162-81479"
    if "speech therapy" in name: return "92507"
    if "wound care" in name: return "97597-97610"
    if "hospice" in name or "palliative" in name: return "99377-99378"
    if "emergency" in name: return "99281-99285"
    if "pediatric" in name: return "99381-99397"

    return "99499" # Unlisted evaluation and management service

def extract_and_validate_code(guessed_code: str, valid_codes_set: set) -> str | None:
    """Extracts the first code from a guess and validates it against the master set."""
    if not guessed_code:
        return None
    
    code_to_validate = guessed_code.split('-')[0].strip()
    
    if code_to_validate in valid_codes_set:
        return code_to_validate
    else:
        return None

class Command(BaseCommand):
    help = 'Fetches referral order types, guesses CPT codes, validates them against a master file, and loads them into the database.'

    def add_arguments(self, parser):
        parser.add_argument('cpt_master_file', type=str, help='The path to the master CPT codes text file (e.g., allCPT_codes.txt).')
        parser.add_argument('--practice_id', type=str, required=True, help='The Athena practice ID.')
        parser.add_argument('--client_id', type=str, required=True, help='Your Athena API Client ID.')
        parser.add_argument('--client_secret', type=str, required=True, help='Your Athena API Client Secret.')

    def handle(self, *args, **options):
        cpt_master_file = options['cpt_master_file']
        practice_id = options['practice_id']
        client_id = options['client_id']
        client_secret = options['client_secret']

        try:
            # Step 1: Parse the master CPT file
            valid_cpt_codes = parse_master_cpt_file(cpt_master_file)

            # Step 2: Fetch all referral order types from Athena
            token = get_token(client_id, client_secret)
            if not token:
                raise CommandError("Could not retrieve API token. Exiting.")
            
            referral_order_types = fetch_all_referral_order_types(practice_id, token)
            if not referral_order_types:
                self.stdout.write(self.style.WARNING("No referral order types found from Athena API. Nothing to process."))
                return

            # Step 3 & 4: Guess, Validate, and Load
            self.stdout.write(self.style.SUCCESS("Starting CPT code guessing, validation, and database loading..."))
            loaded_count = 0
            skipped_count = 0

            for ordertypeid, name in referral_order_types:
                guessed_code = guess_cpt_code(name)
                validated_code = extract_and_validate_code(guessed_code, valid_cpt_codes)

                if validated_code:
                    try:
                        _, created = CPTCodeMapping.objects.update_or_create(
                            referral_order_id=ordertypeid,
                            defaults={
                                'referral_order_name': name,
                                'cpt_code': validated_code,
                                'notes': f"Auto-loaded. Guessed from '{guessed_code}'."
                            }
                        )
                        action = "Created" if created else "Updated"
                        logging.info(f"{action} mapping for '{name}' -> {validated_code}")
                        loaded_count += 1
                    except Exception as e:
                        logging.error(f"Error saving to database for '{name}': {e}")
                        skipped_count += 1
                else:
                    logging.warning(f"Skipping '{name}': Guessed code '{guessed_code}' is not valid or not found in master list.")
                    skipped_count += 1

            self.stdout.write(self.style.SUCCESS("--- All Steps Complete ---"))
            self.stdout.write(self.style.SUCCESS(f"Mappings loaded/updated in database: {loaded_count}"))
            self.stdout.write(self.style.WARNING(f"Mappings skipped: {skipped_count}"))

        except FileNotFoundError:
            raise CommandError(f"Master CPT file not found at '{cpt_master_file}'. Please check the path.")
        except Exception as e:
            raise CommandError(f"An unexpected error occurred: {e}")
