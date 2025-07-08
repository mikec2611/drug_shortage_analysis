import requests, pandas as pd
from tqdm import tqdm

BASE = "https://api.fda.gov/drug/shortages.json"
# API_KEY = "YOUR_OPENFDA_KEY"          # optional but recommended

# ------------------------------------------------------------------
# 1) build the openFDA search query
# ------------------------------------------------------------------
SEARCH_Q = 'status:"Current"' # current shortages only

# ------------------------------------------------------------------
# 2) simple paging helper
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
# 3) main function to pull drug shortage data
# ------------------------------------------------------------------
def get_drug_shortage_data(save_to_csv=True, csv_filename="drug_shortages.csv"):
    """
    Fetch current drug shortage data from the FDA API.
    
    Args:
        save_to_csv (bool): Whether to save the data to a CSV file (default: True)
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
    
    return df

# ------------------------------------------------------------------
# 4) run if called directly
# ------------------------------------------------------------------
if __name__ == "__main__":
    df = get_drug_shortage_data() 