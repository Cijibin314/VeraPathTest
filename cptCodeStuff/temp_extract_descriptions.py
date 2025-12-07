
import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_cpt_descriptions(rvu_data_file: str):
    """
    Extracts CPT codes and their descriptions from the RVU data file.
    """
    if not os.path.exists(rvu_data_file):
        logging.error(f"RVU data file not found at: {rvu_data_file}")
        return {}

    try:
        # Read the file skipping initial garbage rows and manually set headers
        rvu_df = pd.read_csv(rvu_data_file, skiprows=10, header=0)

        # Clean the headers based on previous inspection
        clean_headers = ['HCPCS', 'MOD', 'DESCRIPTION', 'CODE', 'PAYMENT', 'RVU', 'PE RVU', 'INDICATOR', 'PE RVU.1', 'INDICATOR.1', 'RVU.1', 'TOTAL', 'TOTAL.1', 'IND', 'DAYS', 'OP', 'OP.1', 'OP.2', 'PROC', 'SURG', 'SURG.1', 'SURG.2', 'SURG.3', 'BASE', 'FACTOR', 'PROCEDURES', 'FLAG', 'INDICATOR.2', 'AMOUNT', 'AMOUNT.1', 'AMOUNT.2']
        rvu_df.columns = clean_headers
        
        # Select HCPCS and DESCRIPTION
        cpt_descriptions = rvu_df[['HCPCS', 'DESCRIPTION']].set_index('HCPCS').to_dict()['DESCRIPTION']
        
        logging.info(f"Successfully extracted {len(cpt_descriptions)} CPT code descriptions.")
        return cpt_descriptions

    except Exception as e:
        logging.error(f"Error extracting CPT descriptions from '{rvu_data_file}': {e}")
        return {}

if __name__ == "__main__":
    rvu_file_path = os.path.join('cptCodeStuff', 'rvu25a', 'PPRRVU25_JAN.csv')
    descriptions = extract_cpt_descriptions(rvu_file_path)
    
    # Print a few examples
    print("\n--- Example CPT Descriptions ---")
    count = 0
    for code, desc in descriptions.items():
        if count < 10:
            print(f"{code}: {desc}")
            count += 1
        else:
            break
