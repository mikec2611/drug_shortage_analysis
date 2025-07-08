"""
Convenience wrapper for loading drug data to database.
The actual loading functionality has been moved to the respective pull files:
- pull_drug_shortage_data.py: handles shortage data pulling and loading
- pull_drug_enforcement_data.py: handles enforcement data pulling and loading

This file provides convenience functions for loading both datasets at once.
"""

from drug_data_utils import logger
from pull_drug_shortage_data import get_drug_shortage_data
from pull_drug_enforcement_data import get_drug_enforcement_data

def load_drug_shortage_data():
    """
    Load drug shortage data from FDA API to database.
    This is a convenience wrapper around pull_drug_shortage_data.get_drug_shortage_data()
    """
    logger.info("Loading drug shortage data...")
    return get_drug_shortage_data(save_to_csv=True, load_to_database=True)

def load_drug_enforcement_data():
    """
    Load drug enforcement data from FDA API to database.
    This is a convenience wrapper around pull_drug_enforcement_data.get_drug_enforcement_data()
    """
    logger.info("Loading drug enforcement data...")
    return get_drug_enforcement_data(save_to_csv=True, load_to_database=True)

def load_both_datasets():
    """
    Load both drug shortage and enforcement data.
    """
    logger.info("Loading both drug shortage and enforcement datasets...")
    
    logger.info("Step 1/2: Loading drug shortage data...")
    shortage_df = load_drug_shortage_data()
    
    logger.info("Step 2/2: Loading drug enforcement data...")
    enforcement_df = load_drug_enforcement_data()
    
    logger.info("Both datasets loaded successfully!")
    return shortage_df, enforcement_df

if __name__ == "__main__":
    # Load both datasets
    load_both_datasets() 