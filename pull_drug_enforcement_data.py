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

BASE = "https://api.fda.gov/drug/enforcement.json"
# API_KEY = "YOUR_OPENFDA_KEY"          # optional but recommended

# ------------------------------------------------------------------
# 1) build the openFDA search query
# ------------------------------------------------------------------
SEARCH_Q = 'recall_initiation_date:[20200101 TO 20251231]'  # 2020-2025 enforcements

# ------------------------------------------------------------------
# 2) Database table schema
# ------------------------------------------------------------------
ENFORCEMENT_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS drug_enforcement_data (
    id SERIAL PRIMARY KEY,
    status VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(50),
    country VARCHAR(100),
    classification VARCHAR(50),
    product_type VARCHAR(50),
    event_id VARCHAR(50),
    recalling_firm VARCHAR(500),
    address_1 VARCHAR(500),
    address_2 VARCHAR(500),
    postal_code VARCHAR(20),
    voluntary_mandated VARCHAR(100),
    initial_firm_notification VARCHAR(100),
    distribution_pattern TEXT,
    recall_number VARCHAR(50),
    product_description TEXT,
    product_quantity VARCHAR(200),
    reason_for_recall TEXT,
    recall_initiation_date DATE,
    center_classification_date DATE,
    termination_date DATE,
    report_date DATE,
    code_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# ------------------------------------------------------------------
# 3) Data preparation functions
# ------------------------------------------------------------------
def prepare_enforcement_data_for_insert(df):
    """
    Prepare enforcement data DataFrame for database insertion.
    
    Args:
        df: pandas DataFrame with raw enforcement data
        
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
                'status': clean_text_column(row.get('status')),
                'city': clean_text_column(row.get('city')),
                'state': clean_text_column(row.get('state')),
                'country': clean_text_column(row.get('country')),
                'classification': clean_text_column(row.get('classification')),
                'product_type': clean_text_column(row.get('product_type')),
                'event_id': clean_text_column(row.get('event_id')),
                'recalling_firm': clean_text_column(row.get('recalling_firm')),
                'address_1': clean_text_column(row.get('address_1')),
                'address_2': clean_text_column(row.get('address_2')),
                'postal_code': clean_text_column(row.get('postal_code')),
                'voluntary_mandated': clean_text_column(row.get('voluntary_mandated')),
                'initial_firm_notification': clean_text_column(row.get('initial_firm_notification')),
                'distribution_pattern': clean_text_column(row.get('distribution_pattern')),
                'recall_number': clean_text_column(row.get('recall_number')),
                'product_description': clean_text_column(row.get('product_description')),
                'product_quantity': clean_text_column(row.get('product_quantity')),
                'reason_for_recall': clean_text_column(row.get('reason_for_recall')),
                'recall_initiation_date': clean_date_column(row.get('recall_initiation_date'), '%Y%m%d'),
                'center_classification_date': clean_date_column(row.get('center_classification_date'), '%Y%m%d'),
                'termination_date': clean_date_column(row.get('termination_date'), '%Y%m%d'),
                'report_date': clean_date_column(row.get('report_date'), '%Y%m%d'),
                'code_info': clean_text_column(row.get('code_info'))
            }
            prepared_data.append(prepared_row)
        
        return pd.DataFrame(prepared_data)
    
    except Exception as e:
        logger.error(f"Error preparing enforcement data: {e}")
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
# 5) main function to pull drug enforcement data
# ------------------------------------------------------------------
def get_drug_enforcement_data(save_to_csv=True, load_to_database=True, csv_filename="drug_enforcement.csv"):
    """
    Fetch drug enforcement data from the FDA API.
    
    Args:
        save_to_csv (bool): Whether to save the data to a CSV file (default: True)
        load_to_database (bool): Whether to load the data to the database (default: True)
        csv_filename (str): Name of the CSV file to save (default: "drug_enforcement.csv")
    
    Returns:
        pd.DataFrame: DataFrame containing the drug enforcement records
    """
    meta   = fetch_batch(limit=1)["meta"]
    total  = meta["results"]["total"]
    print(f"Total drug enforcement records: {total}")

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
            table_name="drug_enforcement_data",
            table_schema=ENFORCEMENT_TABLE_SCHEMA,
            prepare_data_func=prepare_enforcement_data_for_insert
        )
    
    return df

# ------------------------------------------------------------------
# 6) run if called directly
# ------------------------------------------------------------------
if __name__ == "__main__":
    df = get_drug_enforcement_data() 