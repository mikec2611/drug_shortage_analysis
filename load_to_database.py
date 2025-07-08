import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
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

def drop_and_recreate_table(conn):
    """
    Drop the existing table and recreate it with the updated schema.
    This is needed when column sizes need to be changed.
    
    Args:
        conn: Database connection object
    """
    try:
        cursor = conn.cursor()
        
        # Drop the existing table
        logger.info("Dropping existing drug_shortage_data table...")
        cursor.execute("DROP TABLE IF EXISTS drug_shortage_data;")
        
        # Recreate with new schema
        logger.info("Recreating drug_shortage_data table with updated schema...")
        create_table_if_not_exists(conn)
        
        conn.commit()
        logger.info("Table recreated successfully")
        
    except psycopg2.Error as e:
        logger.error(f"Error dropping/recreating table: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def create_table_if_not_exists(conn):
    """
    Create the drug_shortage_data table if it doesn't exist.
    Updated to match the actual FDA API data structure.
    
    Args:
        conn: Database connection object
    """
    create_table_query = """
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
    
    try:
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        conn.commit()
        logger.info("Table 'drug_shortage_data' created successfully or already exists")
    except psycopg2.Error as e:
        logger.error(f"Error creating table: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def clean_date_column(date_str):
    """
    Clean and convert date strings to proper date format.
    
    Args:
        date_str: Date string from CSV
        
    Returns:
        Cleaned date string or None
    """
    if pd.isna(date_str) or date_str == '' or date_str == 'nan':
        return None
    
    try:
        # Try to parse the date
        parsed_date = pd.to_datetime(date_str, errors='coerce')
        if pd.isna(parsed_date):
            return None
        return parsed_date.date()
    except:
        return None

def clean_text_column(text_str):
    """
    Clean text columns, handling array-like strings and empty values.
    
    Args:
        text_str: Text string from CSV
        
    Returns:
        Cleaned text string or None
    """
    if pd.isna(text_str) or text_str == '' or text_str == 'nan':
        return None
    
    # Convert to string and clean
    text_str = str(text_str)
    
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

def prepare_data_for_insert(csv_file_path):
    """
    Load and prepare data from CSV file for database insertion.
    
    Args:
        csv_file_path: Path to the CSV file
        
    Returns:
        pandas.DataFrame: Prepared data ready for insertion
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        logger.info(f"Successfully loaded CSV file with {len(df)} records")
        
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
        logger.error(f"Error preparing data: {e}")
        raise

def insert_data_to_database(df, conn):
    """
    Insert prepared data into the database using SQLAlchemy for better performance.
    
    Args:
        df: Prepared DataFrame
        conn: Database connection object
    """
    try:
        # Create SQLAlchemy engine
        engine = create_engine(f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        
        # Clear existing data (optional - remove if you want to append)
        with engine.connect() as connection:
            connection.execute(text("DELETE FROM drug_shortage_data"))
            connection.commit()
            logger.info("Cleared existing data from drug_shortage_data table")
        
        # Insert new data
        df.to_sql('drug_shortage_data', engine, if_exists='append', index=False, method='multi')
        logger.info(f"Successfully inserted {len(df)} records into drug_shortage_data table")
        
    except Exception as e:
        logger.error(f"Error inserting data into database: {e}")
        raise

def load_drug_shortage_data():
    """
    Main function to load drug shortage data from CSV into the database.
    """
    csv_file_path = 'drug_shortages.csv'
    
    # Check if CSV file exists
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV file not found: {csv_file_path}")
        logger.info("Please make sure you have run pull_drug_shortage_data.py first to generate the CSV file")
        return
    
    # Check for required environment variables
    if not DB_CONFIG['user'] or not DB_CONFIG['password'] or not DB_CONFIG['host']:
        logger.error("Database credentials not found in .env file")
        logger.info("Please check your .env file has DB_HOST, DB_USER, and DB_PASSWORD")
        return
    
    conn = None
    try:
        # Connect to database
        conn = get_db_connection()
        
        # Drop and recreate table with correct schema
        logger.info("Updating database schema...")
        drop_and_recreate_table(conn)
        
        # Prepare data from CSV
        logger.info("Preparing data from CSV file...")
        df = prepare_data_for_insert(csv_file_path)
        
        # Insert data into database
        logger.info("Inserting data into database...")
        insert_data_to_database(df, conn)
        
        logger.info("Data loading completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during data loading: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    load_drug_shortage_data() 