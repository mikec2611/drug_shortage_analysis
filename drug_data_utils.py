"""
Shared utilities for drug data pulling and loading.
Contains common functions used by both shortage and enforcement data scripts.
"""

import os
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection parameters
DB_CONFIG = {
    'host': os.environ.get('DB_HOST'),
    'port': os.environ.get('DB_PORT'),
    'database': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD')
}

# ------------------------------------------------------------------
# Database helper functions
# ------------------------------------------------------------------

def get_db_connection():
    """
    Create a connection to the PostgreSQL database.
    
    Returns:
        psycopg2.connection: Database connection object
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Successfully connected to PostgreSQL database")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Error connecting to PostgreSQL database: {e}")
        raise

def create_table_if_not_exists(conn, table_name, create_table_query):
    """
    Create a table if it doesn't exist.
    
    Args:
        conn: Database connection object
        table_name: Name of the table to create
        create_table_query: SQL query to create the table
    """
    try:
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        conn.commit()
        logger.info(f"Table '{table_name}' created successfully or already exists")
    except psycopg2.Error as e:
        logger.error(f"Error creating table {table_name}: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def insert_data_to_database(df, table_name, conn):
    """
    Insert prepared data into the database using SQLAlchemy for better performance.
    
    Args:
        df: Prepared DataFrame
        table_name: Name of the table to insert into
        conn: Database connection object
    """
    try:
        # Create SQLAlchemy engine
        engine = create_engine(f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        
        # Clear existing data (full replacement)
        with engine.connect() as connection:
            connection.execute(text(f"DELETE FROM {table_name}"))
            connection.commit()
            logger.info(f"Cleared existing data from {table_name} table")
        
        # Insert new data
        df.to_sql(table_name, engine, if_exists='append', index=False, method='multi')
        logger.info(f"Successfully inserted {len(df)} records into {table_name} table")
        
    except Exception as e:
        logger.error(f"Error inserting data into {table_name}: {e}")
        raise

# ------------------------------------------------------------------
# Data cleaning functions
# ------------------------------------------------------------------

def clean_text_column(text_str):
    """
    Clean text columns, handling array-like strings and empty values.
    
    Args:
        text_str: Text string from CSV
        
    Returns:
        Cleaned text string or None
    """
    # Handle pandas Series/arrays by converting to string first
    if hasattr(text_str, '__len__') and not isinstance(text_str, str):
        # If it's a list or array, join with commas
        if isinstance(text_str, (list, tuple)):
            text_str = ', '.join(str(x) for x in text_str if x is not None)
        else:
            text_str = str(text_str)
    
    # Check for None/NaN/empty after conversion
    if text_str is None or pd.isna(text_str):
        return None
    
    # Convert to string and clean
    text_str = str(text_str)
    
    # Check for empty string or 'nan' string
    if text_str == '' or text_str == 'nan' or text_str.lower() == 'none':
        return None
    
    # If it's an array-like string (starts with [ and ends with ]), 
    # convert it to a more readable format
    if text_str.startswith('[') and text_str.endswith(']'):
        try:
            # Remove brackets and quotes, then join with commas
            cleaned = text_str[1:-1].replace("'", "").replace('"', '')
            return cleaned if cleaned else None
        except:
            return text_str
    
    return text_str

def clean_date_column(date_str, date_format=None):
    """
    Clean and convert date strings to proper date format.
    
    Args:
        date_str: Date string from CSV
        date_format: Optional specific format to try (e.g., '%Y%m%d')
        
    Returns:
        Cleaned date string or None
    """
    # Handle pandas Series/arrays by taking the first element
    if hasattr(date_str, '__len__') and not isinstance(date_str, str):
        if isinstance(date_str, (list, tuple)) and len(date_str) > 0:
            date_str = date_str[0]
        else:
            date_str = str(date_str)
    
    if date_str is None or pd.isna(date_str):
        return None
    
    # Convert to string and check for empty
    date_str = str(date_str).strip()
    if date_str == '' or date_str == 'nan' or date_str.lower() == 'none':
        return None
    
    try:
        # Try specific format first if provided
        if date_format and len(date_str) == len(date_format.replace('%', '')) and date_str.isdigit():
            parsed_date = pd.to_datetime(date_str, format=date_format, errors='coerce')
            if not pd.isna(parsed_date):
                return parsed_date.date()
        
        # Try general parsing
        parsed_date = pd.to_datetime(date_str, errors='coerce')
        if pd.isna(parsed_date):
            return None
        return parsed_date.date()
    except:
        return None

def remove_openfda_fields(df):
    """
    Remove all columns that start with 'openfda' from the DataFrame.
    
    Args:
        df: pandas DataFrame
        
    Returns:
        pandas DataFrame with openfda columns removed
    """
    openfda_columns = [col for col in df.columns if col.startswith('openfda')]
    if openfda_columns:
        logger.info(f"Removing openfda columns: {openfda_columns}")
        df = df.drop(columns=openfda_columns)
    return df

# ------------------------------------------------------------------
# Common workflow functions
# ------------------------------------------------------------------

def check_database_credentials():
    """
    Check if database credentials are available.
    
    Returns:
        bool: True if credentials are available, False otherwise
    """
    if not DB_CONFIG['user'] or not DB_CONFIG['password'] or not DB_CONFIG['host']:
        logger.error("Database credentials not found in .env file")
        logger.info("Please check your .env file has DB_HOST, DB_USER, and DB_PASSWORD")
        return False
    return True

def load_data_to_database(df, table_name, table_schema, prepare_data_func):
    """
    Common workflow for loading data to database.
    
    Args:
        df: Raw DataFrame from API
        table_name: Name of the database table
        table_schema: SQL CREATE TABLE statement
        prepare_data_func: Function to prepare the data for insertion
    """
    if not check_database_credentials():
        logger.info("Skipping database loading...")
        return
    
    conn = None
    try:
        logger.info(f"Loading {table_name} to database...")
        # Connect to database
        conn = get_db_connection()
        
        # Create table
        create_table_if_not_exists(conn, table_name, table_schema)
        
        # Prepare data for insertion
        prepared_df = prepare_data_func(df)
        
        # Insert data into database
        insert_data_to_database(prepared_df, table_name, conn)
        
        logger.info(f"{table_name} loaded to database successfully!")
        
    except Exception as e:
        logger.error(f"Error during {table_name} loading: {e}")
        logger.info("Data was still saved to CSV file")
        raise
    finally:
        if conn:
            conn.close() 