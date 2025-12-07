
import pandas as pd
import os

def get_rvu_values():
    """
    This script reads a list of CPT codes and their descriptions,
    and then merges them with the national RVU data to produce a
    final CSV with all relevant values.
    """
    # Define file paths
    cpt_mappings_file = os.path.join('cptCodeStuff', 'validated_cpt_mappings.csv')
    rvu_data_file = os.path.join('cptCodeStuff', 'rvu25a', 'PPRRVU25_JAN.csv')
    output_file = os.path.join('cptCodeStuff', 'cpt_with_rvus.csv')

    # Check if input files exist
    if not os.path.exists(cpt_mappings_file):
        print(f"Error: CPT mappings file not found at {cpt_mappings_file}")
        return
    if not os.path.exists(rvu_data_file):
        print(f"Error: RVU data file not found at {rvu_data_file}")
        return

    # Read the CPT mappings file
    cpt_df = pd.read_csv(cpt_mappings_file)
    print(f"Successfully loaded {len(cpt_df)} CPT code mappings.")

    # Read the RVU data file, skipping the metadata header rows
    # The actual headers are on row 10 (index 9), but pandas can be tricky.
    # It's safer to read from row 11 (index 10) and assign headers manually.
    rvu_cols = [
        'HCPCS', 'MOD', 'DESCRIPTION', 'STATUS_CODE', 'MEDICARE_PAYMENT',
        'WORK_RVU', 'NON_FAC_PE_RVU', 'NON_FAC_PE_INDICATOR', 'FAC_PE_RVU',
        'FAC_PE_INDICATOR', 'MP_RVU', 'NON_FAC_TOTAL', 'FAC_TOTAL', 'PCTC_IND',
        'GLOB_DAYS', 'PRE_OP', 'INTRA_OP', 'POST_OP', 'MULT_PROC', 'BILAT_SURG',
        'ASST_SURG', 'CO_SURG', 'TEAM_SURG', 'ENDO_BASE', 'CONV_FACTOR',
        'DIAG_PROCEDURES', 'SUPERVISION', 'CALCULATION_FLAG', 'DIAG_IMAGING_FAMILY_INDICATOR',
        'OPPS_PAYMENT_AMOUNT', 'OPPS_PAYMENT_INDICATOR', 'OPPS_PACKAGE_AMOUNT'
    ]
    # Read the file skipping initial garbage rows and manually set headers
    rvu_df = pd.read_csv(rvu_data_file, skiprows=10, header=0)

    # The header names are messed up from the source file. Let's inspect and clean them up.
    # The 10th row is the header, but it's split across multiple lines in the raw file,
    # leading to messy column names in pandas.
    # Let's see what pandas loaded
    print("Columns loaded from RVU file:", rvu_df.columns.tolist())

    # Based on the previous file inspection, the columns we need are:
    # 'HCPCS'
    # 'WORK RVU'
    # 'NON-FAC PE RVU'
    # 'FACILITY PE RVU'
    # 'MP RVU'
    
    # We will need to find the exact column names as read by pandas.
    # Let's assume the names are close to what we saw.
    # A safer approach is to rename them based on position if names are unstable.
    
    # Let's try to find the columns by their expected names, which might be messy.
    # From the file preview, the header line is the 10th line.
    
    # Let's be more robust. We'll read the header row separately and clean it up.
    header_df = pd.read_csv(rvu_data_file, skiprows=9, nrows=1)
    clean_headers = [str(h).strip() for h in header_df.columns]
    print("Cleaned headers:", clean_headers)
    
    rvu_df.columns = clean_headers
    
    # Now select the columns we need with their cleaned names
    required_rvu_cols = {
        'HCPCS': 'cpt_code',
        'RVU': 'work_rvu',
        'PE RVU': 'non_fac_pe_rvu',
        'PE RVU.1': 'fac_pe_rvu',
        'RVU.1': 'mp_rvu'
    }

    # Filter for the columns we need
    rvu_subset_df = rvu_df[list(required_rvu_cols.keys())]
    
    # Rename columns for clarity
    rvu_subset_df = rvu_subset_df.rename(columns=required_rvu_cols)

    # Convert CPT code to string to ensure a safe merge
    rvu_subset_df['cpt_code'] = rvu_subset_df['cpt_code'].astype(str)
    # Rename the column for consistency before the merge
    cpt_df = cpt_df.rename(columns={'validated_cpt_code': 'cpt_code'})
    cpt_df['cpt_code'] = cpt_df['cpt_code'].astype(str)

    # Merge the dataframes
    merged_df = pd.merge(cpt_df, rvu_subset_df, on='cpt_code', how='left')
    
    # Fill NaN values for RVUs with 0, as missing values imply no RVU assigned.
    rvu_columns = ['work_rvu', 'non_fac_pe_rvu', 'fac_pe_rvu', 'mp_rvu']
    for col in rvu_columns:
        if col in merged_df.columns:
            merged_df[col] = merged_df[col].fillna(0)


    # Save the final output
    merged_df.to_csv(output_file, index=False)

    print(f"Successfully merged RVU data.")
    print(f"Output saved to {output_file}")
    print(f"Final dataframe has {len(merged_df)} rows.")
    print("Columns in final output:", merged_df.columns.tolist())


if __name__ == "__main__":
    get_rvu_values()
