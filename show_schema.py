#!/usr/bin/env python3
"""
Script to show the current database schema and sample data.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_CONFIG = {
    'host': os.environ.get('DB_HOST'),
    'port': int(os.environ.get('DB_PORT', 5432)),
    'database': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD')
}

def show_schema():
    """Show the current database schema and sample data."""
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("🗄️  DATABASE SCHEMA")
        print("=" * 60)
        
        # Get table schema
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'drug_shortage_data'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        print(f"Table: drug_shortage_data")
        print(f"Columns: {len(columns)}")
        print("-" * 60)
        
        for col in columns:
            max_len = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"  {col['column_name']:<25} {col['data_type']}{max_len:<15} {nullable}")
        
        # Get record count
        cursor.execute("SELECT COUNT(*) FROM drug_shortage_data;")
        count = cursor.fetchone()['count']
        
        print(f"\n📊 DATA SUMMARY")
        print("=" * 60)
        print(f"Total records: {count}")
        
        # Show sample data
        if count > 0:
            cursor.execute("""
                SELECT proprietary_name, generic_name, company_name, status, shortage_reason
                FROM drug_shortage_data 
                LIMIT 5;
            """)
            
            samples = cursor.fetchall()
            print(f"\n🔍 SAMPLE DATA (first 5 records):")
            print("-" * 60)
            
            for i, sample in enumerate(samples, 1):
                print(f"{i}. {sample['proprietary_name']} ({sample['generic_name']})")
                print(f"   Company: {sample['company_name']}")
                print(f"   Status: {sample['status']}")
                print(f"   Reason: {sample['shortage_reason']}")
                print()
        
        # Show some statistics
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT company_name) as companies,
                COUNT(DISTINCT therapeutic_category) as categories,
                COUNT(DISTINCT status) as statuses
            FROM drug_shortage_data;
        """)
        
        stats = cursor.fetchone()
        print(f"📈 STATISTICS:")
        print(f"  Unique companies: {stats['companies']}")
        print(f"  Therapeutic categories: {stats['categories']}")
        print(f"  Status types: {stats['statuses']}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    show_schema() 