import requests, pandas as pd
from tqdm import tqdm
from drug_data_utils import (
    get_db_connection, 
    create_table_if_not_exists, 
    insert_data_to_database,
    clean_text_column,
    clean_date_column,
    remove_openfda_fields,
    check_database_credentials,
    load_data_to_database,
    logger
)

BASE = "https://api.fda.gov/drug/shortages.json"
# API_KEY = "YOUR_OPENFDA_KEY"          # optional but recommended

# ------------------------------------------------------------------
# 1) build the openFDA search query
# ------------------------------------------------------------------
SEARCH_Q = 'initial_posting_date:[2020-01-01 TO 2025-12-31]' # 2020-2025 shortages

# ------------------------------------------------------------------
# 2) Database table schema
# ------------------------------------------------------------------
SHORTAGE_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS drug_shortage_data (
    id SERIAL PRIMARY KEY,
    update_type VARCHAR(50),
    initial_posting_date DATE,
    proprietary_name VARCHAR(200),
    strength VARCHAR(500),
    package_ndc VARCHAR(50),
    generic_name VARCHAR(200),
    contact_info VARCHAR(200),
    availability VARCHAR(200),
    update_date DATE,
    therapeutic_category VARCHAR(200),
    dosage_form VARCHAR(50),
    presentation VARCHAR(500),
    company_name VARCHAR(100),
    status VARCHAR(50),
    related_info VARCHAR(500),
    shortage_reason VARCHAR(100),
    change_date DATE,
    related_info_link TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# ------------------------------------------------------------------
# 3) Data preparation functions
# ------------------------------------------------------------------
def prepare_shortage_data_for_insert(df):
    """
    Prepare shortage data DataFrame for database insertion.
    
    Args:
        df: pandas DataFrame with raw shortage data
        
    Returns:
        pandas.DataFrame: Prepared data ready for insertion
    """
    try:
        # Remove openfda fields
        df = remove_openfda_fields(df)
        
        # Clean and prepare the data
        prepared_data = []
        
        for _, row in df.iterrows():
            prepared_row = {
                'update_type': clean_text_column(row.get('update_type')),
                'initial_posting_date': clean_date_column(row.get('initial_posting_date')),
                'proprietary_name': clean_text_column(row.get('proprietary_name')),
                'strength': clean_text_column(row.get('strength')),
                'package_ndc': clean_text_column(row.get('package_ndc')),
                'generic_name': clean_text_column(row.get('generic_name')),
                'contact_info': clean_text_column(row.get('contact_info')),
                'availability': clean_text_column(row.get('availability')),
                'update_date': clean_date_column(row.get('update_date')),
                'therapeutic_category': clean_text_column(row.get('therapeutic_category')),
                'dosage_form': clean_text_column(row.get('dosage_form')),
                'presentation': clean_text_column(row.get('presentation')),
                'company_name': clean_text_column(row.get('company_name')),
                'status': clean_text_column(row.get('status')),
                'related_info': clean_text_column(row.get('related_info')),
                'shortage_reason': clean_text_column(row.get('shortage_reason')),
                'change_date': clean_date_column(row.get('change_date')),
                'related_info_link': clean_text_column(row.get('related_info_link'))
            }
            prepared_data.append(prepared_row)
        
        return pd.DataFrame(prepared_data)
    
    except Exception as e:
        logger.error(f"Error preparing shortage data: {e}")
        raise

# ------------------------------------------------------------------
# 4) API helper functions
# ------------------------------------------------------------------
def fetch_batch(limit=100, skip=0):
    params = {
        "limit": limit,
        "skip":  skip,
        "search": SEARCH_Q,
        # "api_key": API_KEY
    }
    r = requests.get(BASE, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# ------------------------------------------------------------------
# 5) main function to pull drug shortage data
# ------------------------------------------------------------------
def get_drug_shortage_data(save_to_csv=True, load_to_database=True, csv_filename="drug_shortages.csv"):
    """
    Fetch current drug shortage data from the FDA API.
    
    Args:
        save_to_csv (bool): Whether to save the data to a CSV file (default: True)
        load_to_database (bool): Whether to load the data to the database (default: True)
        csv_filename (str): Name of the CSV file to save (default: "drug_shortages.csv")
    
    Returns:
        pd.DataFrame: DataFrame containing the drug shortage records
    """
    meta   = fetch_batch(limit=1)["meta"]
    total  = meta["results"]["total"]
    print(f"Total drug shortage records: {total}")

    records = []
    for skip in tqdm(range(0, total, 100)):
        records.extend(fetch_batch(limit=100, skip=skip)["results"])

    df = pd.json_normalize(records)
    
    if save_to_csv:
        df.to_csv(csv_filename, index=False)
        print(f"Saved → {csv_filename}")
    
    if load_to_database:
        load_data_to_database(
            df=df,
            table_name="drug_shortage_data",
            table_schema=SHORTAGE_TABLE_SCHEMA,
            prepare_data_func=prepare_shortage_data_for_insert
        )
    
    return df

# ------------------------------------------------------------------
# 6) run if called directly
# ------------------------------------------------------------------
if __name__ == "__main__":
    df = get_drug_shortage_data() 