#!/usr/bin/env python3
"""
Script to fix the database schema for drug_shortage_data table.
This will drop the existing table and recreate it with the correct column sizes.
"""

import os
import psycopg2
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
    'port': int(os.environ.get('DB_PORT', 5432)),
    'database': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD')
}

def get_db_connection():
    """Create a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Database connection established successfully")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def fix_schema():
    """Drop and recreate the drug_shortage_data table with correct schema."""
    
    # Check for required environment variables
    if not DB_CONFIG['user'] or not DB_CONFIG['password'] or not DB_CONFIG['host']:
        logger.error("Database credentials not found in .env file")
        logger.info("Please check your .env file has DB_HOST, DB_USER, and DB_PASSWORD")
        return
    
    conn = None
    try:
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Drop the existing table
        logger.info("Dropping existing drug_shortage_data table...")
        cursor.execute("DROP TABLE IF EXISTS drug_shortage_data;")
        
        # Create new table with correct schema
        logger.info("Creating drug_shortage_data table with updated schema...")
        
        create_table_query = """
        CREATE TABLE drug_shortage_data (
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
        
        cursor.execute(create_table_query)
        conn.commit()
        
        logger.info("✅ Schema fix completed successfully!")
        logger.info("You can now run load_to_database.py to load your data")
        
    except Exception as e:
        logger.error(f"❌ Error fixing schema: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_schema() 