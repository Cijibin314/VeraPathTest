import csv
import logging
import argparse
import re
import requests
import json
import time
import os
import pandas as pd

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constants ---
DEFAULT_CPT_CODE = "97139"
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MAX_ATTEMPTS = 2
RVU_DATA_FILE_PATH = os.path.join('cptCodeStuff', 'rvu25a', 'PPRRVU25_JAN.csv')

def load_cpt_codes_and_descriptions(rvu_data_file: str):
    """
    Loads CPT codes and their descriptions from the RVU data file.
    Returns a tuple: (set of valid CPT codes, dictionary of CPT code to description).
    """
    valid_codes = set()
    cpt_descriptions = {}

    if not os.path.exists(rvu_data_file):
        logging.error(f"RVU data file not found at: {rvu_data_file}")
        return valid_codes, cpt_descriptions

    try:
        # Read the file skipping initial garbage rows and manually set headers
        rvu_df = pd.read_csv(rvu_data_file, skiprows=10, header=0)

        # Clean the headers based on previous inspection
        clean_headers = ['HCPCS', 'MOD', 'DESCRIPTION', 'CODE', 'PAYMENT', 'RVU', 'PE RVU', 'INDICATOR', 'PE RVU.1', 'INDICATOR.1', 'RVU.1', 'TOTAL', 'TOTAL.1', 'IND', 'DAYS', 'OP', 'OP.1', 'OP.2', 'PROC', 'SURG', 'SURG.1', 'SURG.2', 'SURG.3', 'BASE', 'FACTOR', 'PROCEDURES', 'FLAG', 'INDICATOR.2', 'AMOUNT', 'AMOUNT.1', 'AMOUNT.2']
        rvu_df.columns = clean_headers
        
        # Filter out rows where HCPCS is not a 5-digit alphanumeric code or description is missing
        # CPT codes are 5 digits. HCPCS can be alphanumeric but we are looking for CPTs here.
        rvu_df = rvu_df[rvu_df['HCPCS'].astype(str).str.match(r'^\d{5}', na=False)]
        rvu_df = rvu_df.dropna(subset=['HCPCS', 'DESCRIPTION'])

        for index, row in rvu_df.iterrows():
            code = str(row['HCPCS'])
            description = str(row['DESCRIPTION']).strip()
            valid_codes.add(code)
            cpt_descriptions[code] = description
        
        logging.info(f"Successfully loaded {len(valid_codes)} unique CPT codes and descriptions from '{rvu_data_file}'.")
        return valid_codes, cpt_descriptions

    except Exception as e:
        logging.error(f"Error loading CPT descriptions from '{rvu_data_file}': {e}")
        return valid_codes, cpt_descriptions

def get_ai_guess_with_retries(referral_name: str, model_name: str, valid_codes_set: set, cpt_descriptions: dict) -> str | None:
    """
    Uses a local Ollama model to guess a CPT code, with a retry mechanism,
    and includes CPT descriptions in the prompt for plausibility checking.
    """
    base_prompt = (
        "You are a medical coding expert. Your task is to suggest a single, common, 5-digit CPT code for a new patient visit "
        "based on the following referral specialty. Respond with only the 5-digit CPT code and nothing else.\n\n"
        "Consider the semantic relevance of the CPT code's description to the referral specialty. "
        "Avoid codes with descriptions that clearly do not match the referral.\n\n"
        f"Referral: \"{referral_name}\"\n\n"
    )
    
    invalid_guesses = []
    
    for attempt in range(MAX_ATTEMPTS):
        prompt = base_prompt
        if invalid_guesses:
            prompt += f"You previously suggested the following invalid codes: {', '.join(invalid_guesses)}. Do not choose from that list.\n"
        
        # Add description for context if the AI provides a guess
        if attempt > 0 and guessed_code_prev_attempt: # only add description if there was a previous guess to provide context
            if guessed_code_prev_attempt in cpt_descriptions:
                prompt += f"Consider the description of '{guessed_code_prev_attempt}': '{cpt_descriptions[guessed_code_prev_attempt]}'\n"
            else:
                prompt += f"Previous guess '{guessed_code_prev_attempt}' was not found in our master list.\n"

        prompt += "CPT Code:"

        payload = {"model": model_name, "prompt": prompt, "stream": False}

        try:
            response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
            response.raise_for_status()
            response_data = response.json()
            guessed_code_raw = response_data.get("response", "").strip()

            # Clean the response to get only the 5-digit code
            match = re.search(r'\b\d{5}\b', guessed_code_raw)
            guessed_code_prev_attempt = None # Reset for next attempt's context

            if match:
                guessed_code = match.group(0)
                guessed_code_prev_attempt = guessed_code
                # Validate against the master list
                if guessed_code in valid_codes_set:
                    logging.info(f"Attempt {attempt + 1}: AI returned valid code '{guessed_code}' for '{referral_name}'.")
                    return guessed_code
                else:
                    logging.warning(f"Attempt {attempt + 1}: AI returned '{guessed_code}', which is not in the master list.")
                    invalid_guesses.append(guessed_code)
            else:
                logging.warning(f"Attempt {attempt + 1}: AI response '{guessed_code_raw}' did not contain a 5-digit code.")
                # Add a placeholder to prevent identical retry prompts if response is empty
                invalid_guesses.append(guessed_code_raw if guessed_code_raw else "empty response")

        except requests.exceptions.RequestException as e:
            logging.error(f"Ollama API error on attempt {attempt + 1}: {e}")
            # Wait a moment before retrying on API error
            time.sleep(2)

    logging.error(f"Failed to get a valid CPT code for '{referral_name}' after {MAX_ATTEMPTS} attempts.")
    return None

def run_pass(referrals_to_process, model_name, valid_codes, cpt_descriptions, output_file):
    """Runs a single pass of CPT code guessing and returns the number of defaulted codes."""
    successful_count = 0
    defaulted_count = 0
    
    # Read existing data if the file already exists to update it
    existing_data = {}
    if os.path.exists(output_file):
        with open(output_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_data[row['ordertypeid']] = row

    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['ordertypeid', 'name', 'validated_cpt_code']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Update existing entries that are not being re-processed
        for ordertypeid, data in existing_data.items():
            is_being_reprocessed = any(r['ordertypeid'] == ordertypeid for r in referrals_to_process)
            if not is_being_reprocessed:
                writer.writerow(data)

        for i, referral_type in enumerate(referrals_to_process):
            name = referral_type.get('name')
            ordertypeid = referral_type.get('ordertypeid')
            logging.info(f"Processing ({i+1}/{len(referrals_to_process)}): {name}")

            if not name or not ordertypeid: continue

            ai_selected_code = get_ai_guess_with_retries(name, model_name, valid_codes, cpt_descriptions)
            
            final_code = ai_selected_code if ai_selected_code else DEFAULT_CPT_CODE
            writer.writerow({'ordertypeid': ordertypeid, 'name': name, 'validated_cpt_code': final_code})

            if ai_selected_code:
                successful_count += 1
            else:
                defaulted_count += 1
    
    logging.info(f"Pass complete. Successful guesses: {successful_count}, Defaulted: {defaulted_count}")
    return defaulted_count


def main():
    parser = argparse.ArgumentParser(description='Guess and validate CPT codes using a local Ollama model with retries.')
    parser.add_argument('--referral_types_csv', type=str, help='Path to the referral_order_types.csv file for an initial run.')
    parser.add_argument('--ollama_model', type=str, default='llama3', help='The name of the Ollama model to use.')
    parser.add_argument('--output_file', type=str, default=os.path.join('cptCodeStuff', 'validated_cpt_mappings.csv'), help='The final CSV file with validated mappings.')
    parser.add_argument('--continue_from_previous', action='store_true', help='Continue processing from a previous run.')
    args = parser.parse_args()

    try:
        valid_cpt_codes, cpt_descriptions = load_cpt_codes_and_descriptions(RVU_DATA_FILE_PATH)
        if DEFAULT_CPT_CODE not in valid_cpt_codes:
            logging.warning(f"Default CPT code '{DEFAULT_CPT_CODE}' not in master list. Please verify.")

        defaulted_count = 0

        if not args.continue_from_previous:
            # --- Initial Pass ---
            if not args.referral_types_csv:
                logging.error("The --referral_types_csv argument is required for an initial run.")
                return
            with open(args.referral_types_csv, 'r', newline='') as infile:
                all_referral_types = list(csv.DictReader(infile))
            logging.info(f"Loaded {len(all_referral_types)} referral types from '{args.referral_types_csv}'.")
            
            logging.info("--- Starting Initial Pass ---")
            defaulted_count = run_pass(all_referral_types, args.ollama_model, valid_cpt_codes, cpt_descriptions, args.output_file)
        else:
            # --- Continuation Pass ---
            if not os.path.exists(args.output_file):
                logging.error(f"Output file '{args.output_file}' not found. Cannot continue from previous run.")
                return

            referrals_to_reprocess = []
            with open(args.output_file, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row['validated_cpt_code'] == DEFAULT_CPT_CODE:
                        referrals_to_reprocess.append(row)

            if not referrals_to_reprocess:
                logging.info("No more referrals with default codes to process.")
                defaulted_count = 0
            else:
                logging.info(f"--- Starting Continuation Pass ---")
                logging.info(f"There are currently {len(referrals_to_reprocess)} referrals with the default code. Attempting to re-process.")
                defaulted_count = run_pass(referrals_to_reprocess, args.ollama_model, valid_cpt_codes, cpt_descriptions, args.output_file)
            
        logging.info("--- Pass Complete ---")
        logging.info(f"Final count of mappings with default code: {defaulted_count}")
        if defaulted_count >= 50:
            logging.warning("There are still 50 or more mappings with the default code. Another pass may be required.")

    except FileNotFoundError:
        logging.error("Input file not found. Please check paths.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()