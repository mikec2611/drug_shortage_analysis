#!/usr/bin/env python3
"""
Script to extract drug shortage and enforcement data from PostgreSQL database for analysis.
This script pulls both datasets and prepares them for further analysis.
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from drug_data_utils import DB_CONFIG, get_db_connection, check_database_credentials, logger
from datetime import datetime

def extract_drug_shortage_data(conn=None, filters=None):
    """
    Extract drug shortage data from PostgreSQL database.
    
    Args:
        conn: Database connection object (optional, will create if not provided)
        filters: Dictionary of filters to apply (optional)
            - date_from: Start date filter (YYYY-MM-DD)
            - date_to: End date filter (YYYY-MM-DD)
            - status: Status filter
            - company_name: Company name filter
    
    Returns:
        pandas.DataFrame: Drug shortage data
    """
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True
    
    try:
        # Base query
        query = """
        SELECT 
            id,
            update_type,
            initial_posting_date,
            proprietary_name,
            strength,
            package_ndc,
            generic_name,
            contact_info,
            availability,
            update_date,
            therapeutic_category,
            dosage_form,
            presentation,
            company_name,
            status,
            related_info,
            shortage_reason,
            change_date,
            related_info_link,
            created_at,
            updated_at
        FROM drug_shortage_data
        """
        
        # Add filters if provided
        where_conditions = []
        params = []
        
        if filters:
            if filters.get('date_from'):
                where_conditions.append("initial_posting_date >= %s")
                params.append(filters['date_from'])
            
            if filters.get('date_to'):
                where_conditions.append("initial_posting_date <= %s")
                params.append(filters['date_to'])
            
            if filters.get('status'):
                where_conditions.append("status = %s")
                params.append(filters['status'])
            
            if filters.get('company_name'):
                where_conditions.append("company_name ILIKE %s")
                params.append(f"%{filters['company_name']}%")
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        query += " ORDER BY initial_posting_date DESC"
        
        logger.info(f"Executing shortage data query with {len(params)} filters")
        
        # Execute query
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        logger.info(f"Retrieved {len(df)} shortage records")
        
        return df
        
    except Exception as e:
        logger.error(f"Error extracting shortage data: {e}")
        raise
    finally:
        if close_conn and conn:
            conn.close()

def extract_drug_enforcement_data(conn=None, filters=None):
    """
    Extract drug enforcement data from PostgreSQL database.
    
    Args:
        conn: Database connection object (optional, will create if not provided)
        filters: Dictionary of filters to apply (optional)
            - date_from: Start date filter (YYYY-MM-DD)
            - date_to: End date filter (YYYY-MM-DD)
            - classification: Classification filter
            - state: State filter
            - recalling_firm: Recalling firm filter
    
    Returns:
        pandas.DataFrame: Drug enforcement data
    """
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True
    
    try:
        # Base query
        query = """
        SELECT 
            id,
            status,
            city,
            state,
            country,
            classification,
            product_type,
            event_id,
            recalling_firm,
            address_1,
            address_2,
            postal_code,
            voluntary_mandated,
            initial_firm_notification,
            distribution_pattern,
            recall_number,
            product_description,
            product_quantity,
            reason_for_recall,
            recall_initiation_date,
            center_classification_date,
            termination_date,
            report_date,
            code_info,
            created_at,
            updated_at
        FROM drug_enforcement_data
        """
        
        # Add filters if provided
        where_conditions = []
        params = []
        
        if filters:
            if filters.get('date_from'):
                where_conditions.append("recall_initiation_date >= %s")
                params.append(filters['date_from'])
            
            if filters.get('date_to'):
                where_conditions.append("recall_initiation_date <= %s")
                params.append(filters['date_to'])
            
            if filters.get('classification'):
                where_conditions.append("classification = %s")
                params.append(filters['classification'])
            
            if filters.get('state'):
                where_conditions.append("state = %s")
                params.append(filters['state'])
            
            if filters.get('recalling_firm'):
                where_conditions.append("recalling_firm ILIKE %s")
                params.append(f"%{filters['recalling_firm']}%")
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        query += " ORDER BY recall_initiation_date DESC"
        
        logger.info(f"Executing enforcement data query with {len(params)} filters")
        
        # Execute query
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        logger.info(f"Retrieved {len(df)} enforcement records")
        
        return df
        
    except Exception as e:
        logger.error(f"Error extracting enforcement data: {e}")
        raise
    finally:
        if close_conn and conn:
            conn.close()

def extract_both_datasets(shortage_filters=None, enforcement_filters=None):
    """
    Extract both drug shortage and enforcement datasets with a single connection.
    
    Args:
        shortage_filters: Dictionary of filters for shortage data
        enforcement_filters: Dictionary of filters for enforcement data
    
    Returns:
        tuple: (shortage_df, enforcement_df)
    """
    if not check_database_credentials():
        raise ValueError("Database credentials not found. Please check your .env file.")
    
    conn = None
    try:
        logger.info("Connecting to database for data extraction...")
        conn = get_db_connection()
        
        # Extract shortage data
        logger.info("Extracting drug shortage data...")
        shortage_df = extract_drug_shortage_data(conn, shortage_filters)
        
        # Extract enforcement data
        logger.info("Extracting drug enforcement data...")
        enforcement_df = extract_drug_enforcement_data(conn, enforcement_filters)
        
        logger.info("Data extraction completed successfully")
        
        return shortage_df, enforcement_df
        
    except Exception as e:
        logger.error(f"Error during data extraction: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_data_summary():
    """
    Get a summary of both datasets including record counts and date ranges.
    
    Returns:
        dict: Summary statistics for both datasets
    """
    if not check_database_credentials():
        raise ValueError("Database credentials not found. Please check your .env file.")
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get shortage data summary
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                MIN(initial_posting_date) as earliest_date,
                MAX(initial_posting_date) as latest_date,
                COUNT(DISTINCT company_name) as unique_companies,
                COUNT(DISTINCT status) as unique_statuses,
                COUNT(DISTINCT therapeutic_category) as unique_categories
            FROM drug_shortage_data
        """)
        shortage_summary = cursor.fetchone()
        
        # Get enforcement data summary
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                MIN(recall_initiation_date) as earliest_date,
                MAX(recall_initiation_date) as latest_date,
                COUNT(DISTINCT recalling_firm) as unique_firms,
                COUNT(DISTINCT classification) as unique_classifications,
                COUNT(DISTINCT state) as unique_states
            FROM drug_enforcement_data
        """)
        enforcement_summary = cursor.fetchone()
        
        summary = {
            'shortage_data': dict(shortage_summary),
            'enforcement_data': dict(enforcement_summary),
            'extraction_timestamp': datetime.now().isoformat()
        }
        
        logger.info("Data summary retrieved successfully")
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting data summary: {e}")
        raise
    finally:
        if conn:
            conn.close()

def save_datasets_to_csv(shortage_df, enforcement_df, shortage_filename="shortage_analysis.csv", enforcement_filename="enforcement_analysis.csv"):
    """
    Save extracted datasets to CSV files.
    
    Args:
        shortage_df: DataFrame with shortage data
        enforcement_df: DataFrame with enforcement data
        shortage_filename: Output filename for shortage data
        enforcement_filename: Output filename for enforcement data
    """
    try:
        shortage_df.to_csv(shortage_filename, index=False)
        logger.info(f"Shortage data saved to {shortage_filename}")
        
        enforcement_df.to_csv(enforcement_filename, index=False)
        logger.info(f"Enforcement data saved to {enforcement_filename}")
        
    except Exception as e:
        logger.error(f"Error saving datasets to CSV: {e}")
        raise

if __name__ == "__main__":
    # Example usage
    print("🔍 Drug Data Extraction for Analysis")
    print("=" * 50)
    
    # Get data summary
    print("📊 Getting data summary...")
    summary = get_data_summary()
    
    print(f"\n📋 SHORTAGE DATA SUMMARY:")
    print(f"  Total records: {summary['shortage_data']['total_records']:,}")
    print(f"  Date range: {summary['shortage_data']['earliest_date']} to {summary['shortage_data']['latest_date']}")
    print(f"  Unique companies: {summary['shortage_data']['unique_companies']}")
    print(f"  Unique statuses: {summary['shortage_data']['unique_statuses']}")
    print(f"  Therapeutic categories: {summary['shortage_data']['unique_categories']}")
    
    print(f"\n📋 ENFORCEMENT DATA SUMMARY:")
    print(f"  Total records: {summary['enforcement_data']['total_records']:,}")
    print(f"  Date range: {summary['enforcement_data']['earliest_date']} to {summary['enforcement_data']['latest_date']}")
    print(f"  Unique firms: {summary['enforcement_data']['unique_firms']}")
    print(f"  Unique classifications: {summary['enforcement_data']['unique_classifications']}")
    print(f"  Unique states: {summary['enforcement_data']['unique_states']}")
    
    # Extract both datasets
    print(f"\n🔄 Extracting both datasets...")
    shortage_df, enforcement_df = extract_both_datasets()
    
    # Save to CSV
    print(f"\n💾 Saving datasets to CSV...")
    save_datasets_to_csv(shortage_df, enforcement_df)
    
    print(f"\n✅ Data extraction completed successfully!")
    print(f"   - Shortage records: {len(shortage_df):,}")
    print(f"   - Enforcement records: {len(enforcement_df):,}") 