#!/usr/bin/env python3
"""
Create dashboard datasets from drug shortage and enforcement data.
This script pulls data from the main tables and creates aggregated datasets
optimized for dashboard visualization and analysis.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from sqlalchemy import create_engine, text
import logging
from dotenv import load_dotenv
from drug_data_utils import get_db_connection, DB_CONFIG, logger

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DashboardDatasetCreator:
    """Create and manage dashboard datasets from drug shortage and enforcement data."""
    
    def __init__(self):
        self.engine = create_engine(f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    
    def execute_sql(self, query, description=""):
        """Execute SQL query and return results."""
        try:
            with self.engine.connect() as conn:
                trans = conn.begin()
                try:
                    result = conn.execute(text(query))
                    trans.commit()
                    if description:
                        logger.info(f"Executed: {description}")
                    return result
                except Exception as e:
                    trans.rollback()
                    logger.error(f"SQL Error in {description}: {e}")
                    logger.error(f"Query: {query[:200]}..." if len(query) > 200 else f"Query: {query}")
                    raise
        except Exception as e:
            logger.error(f"Connection error ({description}): {e}")
            raise
    
    def create_table_from_query(self, table_name, query, description=""):
        """Create a new table from a SQL query."""
        try:
            # Drop existing table
            drop_query = f"DROP TABLE IF EXISTS {table_name};"
            self.execute_sql(drop_query, f"Dropping existing {table_name}")
            
            # Create new table with explicit commit
            create_query = f"CREATE TABLE {table_name} AS ({query});"
            with self.engine.connect() as conn:
                trans = conn.begin()
                try:
                    conn.execute(text(create_query))
                    trans.commit()
                    logger.info(f"Created table: {table_name}")
                except Exception as e:
                    trans.rollback()
                    logger.error(f"Error in CREATE TABLE query for {table_name}: {e}")
                    raise
            
            # Verify table was created and add timestamp
            verify_query = f"SELECT COUNT(*) FROM {table_name};"
            result = self.execute_sql(verify_query, f"Verifying {table_name}")
            row_count = result.fetchone()[0]
            
            # Add created_at timestamp
            alter_query = f"ALTER TABLE {table_name} ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"
            self.execute_sql(alter_query, f"Adding timestamp to {table_name}")
            
            logger.info(f"✅ Created table: {table_name} - {description} ({row_count} records)")
            
        except Exception as e:
            logger.error(f"❌ Error creating {table_name}: {e}")
            raise
    
    def create_monthly_trends_dataset(self):
        """Create monthly trends dataset combining shortages and enforcements."""
        # Debug: Check status values and June 2025 data
        debug_query = """
        SELECT 
            DATE_TRUNC('month', initial_posting_date) as month,
            status,
            COUNT(*) as count
        FROM drug_shortage_data 
        WHERE DATE_TRUNC('month', initial_posting_date) = '2025-06-01'
        GROUP BY DATE_TRUNC('month', initial_posting_date), status
        ORDER BY count DESC;
        """
        
        try:
            debug_result = self.execute_sql(debug_query, "Debugging June 2025 data")
            logger.info("🔍 June 2025 status breakdown:")
            for row in debug_result:
                logger.info(f"   Status: {row[1]} | Count: {row[2]}")
        except Exception as e:
            logger.warning(f"⚠️ Debug query failed: {e}")
        
        # Main query - include ALL records for monthly trends
        query = """
        WITH shortage_monthly AS (
            SELECT 
                DATE_TRUNC('month', initial_posting_date) as month,
                COUNT(*) as shortage_count,
                COUNT(DISTINCT company_name) as companies_with_shortages,
                COUNT(DISTINCT therapeutic_category) as affected_categories
            FROM drug_shortage_data 
            WHERE initial_posting_date IS NOT NULL
            GROUP BY DATE_TRUNC('month', initial_posting_date)
        ),
        enforcement_monthly AS (
            SELECT 
                DATE_TRUNC('month', recall_initiation_date) as month,
                COUNT(*) as enforcement_count,
                COUNT(DISTINCT recalling_firm) as companies_with_enforcements,
                COUNT(DISTINCT classification) as enforcement_types
            FROM drug_enforcement_data 
            WHERE recall_initiation_date IS NOT NULL
            GROUP BY DATE_TRUNC('month', recall_initiation_date)
        )
        SELECT 
            COALESCE(s.month, e.month) as month,
            COALESCE(s.shortage_count, 0) as shortage_count,
            COALESCE(e.enforcement_count, 0) as enforcement_count,
            COALESCE(s.companies_with_shortages, 0) as companies_with_shortages,
            COALESCE(e.companies_with_enforcements, 0) as companies_with_enforcements,
            COALESCE(s.affected_categories, 0) as affected_categories,
            COALESCE(e.enforcement_types, 0) as enforcement_types,
            (COALESCE(s.shortage_count, 0) + COALESCE(e.enforcement_count, 0)) as total_issues
        FROM shortage_monthly s
        FULL OUTER JOIN enforcement_monthly e ON s.month = e.month
        ORDER BY month
        """
        
        self.create_table_from_query(
            "dashboard_monthly_trends", 
            query, 
            "Monthly trends of drug issues"
        )
    
    def create_company_analysis_dataset(self):
        """Create comprehensive company analysis dataset."""
        query = """
        WITH company_shortages AS (
            SELECT 
                company_name,
                COUNT(*) as shortage_count,
                COUNT(DISTINCT therapeutic_category) as categories_affected,
                COUNT(DISTINCT generic_name) as drugs_affected,
                COUNT(CASE WHEN status = 'Current' THEN 1 END) as current_shortages,
                COUNT(CASE WHEN status = 'Resolved' THEN 1 END) as resolved_shortages,
                MIN(initial_posting_date) as first_shortage_date,
                MAX(initial_posting_date) as latest_shortage_date
            FROM drug_shortage_data 
            WHERE company_name IS NOT NULL
            GROUP BY company_name
        ),
        company_enforcements AS (
            SELECT 
                recalling_firm as company_name,
                COUNT(*) as enforcement_count,
                COUNT(DISTINCT classification) as enforcement_types,
                COUNT(CASE WHEN classification = 'Class I' THEN 1 END) as class_i_recalls,
                COUNT(CASE WHEN classification = 'Class II' THEN 1 END) as class_ii_recalls,
                COUNT(CASE WHEN classification = 'Class III' THEN 1 END) as class_iii_recalls,
                COUNT(CASE WHEN status = 'Ongoing' THEN 1 END) as ongoing_recalls,
                MIN(recall_initiation_date) as first_recall_date,
                MAX(recall_initiation_date) as latest_recall_date
            FROM drug_enforcement_data 
            WHERE recalling_firm IS NOT NULL
            GROUP BY recalling_firm
        )
        SELECT 
            COALESCE(s.company_name, e.company_name) as company_name,
            COALESCE(s.shortage_count, 0) as shortage_count,
            COALESCE(e.enforcement_count, 0) as enforcement_count,
            COALESCE(s.categories_affected, 0) as categories_affected,
            COALESCE(s.drugs_affected, 0) as drugs_affected,
            COALESCE(s.current_shortages, 0) as current_shortages,
            COALESCE(s.resolved_shortages, 0) as resolved_shortages,
            COALESCE(e.enforcement_types, 0) as enforcement_types,
            COALESCE(e.class_i_recalls, 0) as class_i_recalls,
            COALESCE(e.class_ii_recalls, 0) as class_ii_recalls,
            COALESCE(e.class_iii_recalls, 0) as class_iii_recalls,
            COALESCE(e.ongoing_recalls, 0) as ongoing_recalls,
            (COALESCE(s.shortage_count, 0) + COALESCE(e.enforcement_count, 0)) as total_issues,
            CASE 
                WHEN s.shortage_count > 0 AND e.enforcement_count > 0 THEN 'Both Issues'
                WHEN s.shortage_count > 0 THEN 'Shortage Only'
                WHEN e.enforcement_count > 0 THEN 'Enforcement Only'
                ELSE 'No Issues'
            END as issue_type,
            s.first_shortage_date,
            s.latest_shortage_date,
            e.first_recall_date,
            e.latest_recall_date
        FROM company_shortages s
        FULL OUTER JOIN company_enforcements e ON s.company_name = e.company_name
        ORDER BY total_issues DESC
        """
        
        self.create_table_from_query(
            "dashboard_company_analysis", 
            query, 
            "Company-level analysis of drug issues"
        )
    
    def create_therapeutic_category_analysis_dataset(self):
        """Create therapeutic category analysis dataset."""
        query = """
        SELECT 
            therapeutic_category,
            COUNT(*) as shortage_count,
            COUNT(DISTINCT company_name) as companies_affected,
            COUNT(DISTINCT generic_name) as drugs_affected,
            COUNT(CASE WHEN status = 'Current' THEN 1 END) as current_shortages,
            COUNT(CASE WHEN status = 'Resolved' THEN 1 END) as resolved_shortages,
            ROUND(
                COUNT(CASE WHEN status = 'Current' THEN 1 END) * 100.0 / COUNT(*), 
                2
            ) as current_shortage_percentage,
            MIN(initial_posting_date) as first_shortage_date,
            MAX(initial_posting_date) as latest_shortage_date,
            MODE() WITHIN GROUP (ORDER BY shortage_reason) as most_common_reason
        FROM drug_shortage_data 
        WHERE therapeutic_category IS NOT NULL
        GROUP BY therapeutic_category
        ORDER BY shortage_count DESC
        """
        
        self.create_table_from_query(
            "dashboard_therapeutic_categories", 
            query, 
            "Therapeutic category analysis"
        )
    
    def create_geographic_analysis_dataset(self):
        """Create geographic analysis of enforcement actions."""
        query = """
        SELECT 
            state,
            country,
            COUNT(*) as enforcement_count,
            COUNT(DISTINCT recalling_firm) as companies_affected,
            COUNT(CASE WHEN classification = 'Class I' THEN 1 END) as class_i_recalls,
            COUNT(CASE WHEN classification = 'Class II' THEN 1 END) as class_ii_recalls,
            COUNT(CASE WHEN classification = 'Class III' THEN 1 END) as class_iii_recalls,
            COUNT(CASE WHEN status = 'Ongoing' THEN 1 END) as ongoing_recalls,
            ROUND(
                COUNT(CASE WHEN classification = 'Class I' THEN 1 END) * 100.0 / COUNT(*), 
                2
            ) as class_i_percentage,
            MIN(recall_initiation_date) as first_recall_date,
            MAX(recall_initiation_date) as latest_recall_date
        FROM drug_enforcement_data 
        WHERE state IS NOT NULL
        GROUP BY state, country
        ORDER BY enforcement_count DESC
        """
        
        self.create_table_from_query(
            "dashboard_geographic_analysis", 
            query, 
            "Geographic analysis of enforcement actions"
        )
    
    def create_top_drugs_dataset(self):
        """Create analysis of most frequently affected drugs."""
        query = """
        WITH drug_shortages AS (
            SELECT 
                generic_name,
                proprietary_name,
                COUNT(*) as shortage_count,
                COUNT(DISTINCT company_name) as companies_affected,
                COUNT(CASE WHEN status = 'Current' THEN 1 END) as current_shortages,
                therapeutic_category,
                MODE() WITHIN GROUP (ORDER BY shortage_reason) as most_common_reason,
                MIN(initial_posting_date) as first_shortage_date,
                MAX(initial_posting_date) as latest_shortage_date
            FROM drug_shortage_data 
            WHERE generic_name IS NOT NULL
            GROUP BY generic_name, proprietary_name, therapeutic_category
        )
        SELECT 
            generic_name,
            proprietary_name,
            therapeutic_category,
            shortage_count,
            companies_affected,
            current_shortages,
            most_common_reason,
            first_shortage_date,
            latest_shortage_date,
            CASE 
                WHEN current_shortages > 0 THEN 'Currently in shortage'
                ELSE 'No current shortage'
            END as current_status
        FROM drug_shortages
        ORDER BY shortage_count DESC, current_shortages DESC
        """
        
        self.create_table_from_query(
            "dashboard_top_drugs", 
            query, 
            "Most frequently affected drugs"
        )
    
    def create_shortage_reasons_dataset(self):
        """Create analysis of shortage reasons."""
        query = """
        SELECT 
            shortage_reason,
            COUNT(*) as occurrence_count,
            COUNT(DISTINCT company_name) as companies_affected,
            COUNT(DISTINCT therapeutic_category) as categories_affected,
            COUNT(DISTINCT generic_name) as drugs_affected,
            COUNT(CASE WHEN status = 'Current' THEN 1 END) as current_shortages,
            ROUND(
                COUNT(CASE WHEN status = 'Current' THEN 1 END) * 100.0 / COUNT(*), 
                2
            ) as current_shortage_percentage,
            MIN(initial_posting_date) as first_occurrence,
            MAX(initial_posting_date) as latest_occurrence
        FROM drug_shortage_data 
        WHERE shortage_reason IS NOT NULL
        GROUP BY shortage_reason
        ORDER BY occurrence_count DESC
        """
        
        self.create_table_from_query(
            "dashboard_shortage_reasons", 
            query, 
            "Analysis of shortage reasons"
        )
    
    def create_recall_severity_dataset(self):
        """Create analysis of recall severity and classifications."""
        query = """
        SELECT 
            classification,
            COUNT(*) as recall_count,
            COUNT(DISTINCT recalling_firm) as companies_affected,
            COUNT(CASE WHEN status = 'Ongoing' THEN 1 END) as ongoing_recalls,
            COUNT(CASE WHEN status = 'Completed' THEN 1 END) as completed_recalls,
            ROUND(
                COUNT(CASE WHEN status = 'Ongoing' THEN 1 END) * 100.0 / COUNT(*), 
                2
            ) as ongoing_percentage,
            MIN(recall_initiation_date) as first_recall_date,
            MAX(recall_initiation_date) as latest_recall_date,
            MODE() WITHIN GROUP (ORDER BY reason_for_recall) as most_common_reason
        FROM drug_enforcement_data 
        WHERE classification IS NOT NULL
        GROUP BY classification
        ORDER BY 
            CASE classification 
                WHEN 'Class I' THEN 1 
                WHEN 'Class II' THEN 2 
                WHEN 'Class III' THEN 3 
                ELSE 4 
            END
        """
        
        self.create_table_from_query(
            "dashboard_recall_severity", 
            query, 
            "Recall severity and classification analysis"
        )
    
    def create_recent_activity_dataset(self):
        """Create dataset showing recent activity across both shortage and enforcement data."""
        query = """
        WITH recent_shortages AS (
            SELECT 
                'Shortage' as issue_type,
                initial_posting_date as issue_date,
                company_name as company,
                generic_name as drug_name,
                therapeutic_category as category,
                status,
                shortage_reason as reason,
                'N/A' as classification
            FROM drug_shortage_data 
            WHERE initial_posting_date >= CURRENT_DATE - INTERVAL '90 days'
        ),
        recent_enforcements AS (
            SELECT 
                'Enforcement' as issue_type,
                recall_initiation_date as issue_date,
                recalling_firm as company,
                product_description as drug_name,
                'N/A' as category,
                status,
                reason_for_recall as reason,
                classification
            FROM drug_enforcement_data 
            WHERE recall_initiation_date >= CURRENT_DATE - INTERVAL '90 days'
        )
        SELECT * FROM recent_shortages
        UNION ALL
        SELECT * FROM recent_enforcements
        ORDER BY issue_date DESC
        """
        
        self.create_table_from_query(
            "dashboard_recent_activity", 
            query, 
            "Recent activity (last 90 days)"
        )
    
    def create_summary_metrics_dataset(self):
        """Create high-level summary metrics for dashboard overview."""
        # Debug: Check all status values in the data
        debug_status_query = """
        SELECT status, COUNT(*) as count 
        FROM drug_shortage_data 
        GROUP BY status 
        ORDER BY count DESC;
        """
        
        try:
            debug_result = self.execute_sql(debug_status_query, "Debugging all status values")
            logger.info("🔍 All status values in drug shortage data:")
            for row in debug_result:
                logger.info(f"   Status: '{row[0]}' | Count: {row[1]}")
        except Exception as e:
            logger.warning(f"⚠️ Debug status query failed: {e}")
            
        # Debug: Check recent data including June 2025
        debug_recent_query = """
        SELECT 
            DATE_TRUNC('month', initial_posting_date) as month,
            status,
            COUNT(*) as count 
        FROM drug_shortage_data 
        WHERE initial_posting_date >= '2025-06-01'
        GROUP BY DATE_TRUNC('month', initial_posting_date), status
        ORDER BY month DESC, count DESC;
        """
        
        try:
            debug_result = self.execute_sql(debug_recent_query, "Debugging June 2025+ data")
            logger.info("🔍 June 2025+ status breakdown:")
            for row in debug_result:
                logger.info(f"   Month: {row[0]} | Status: '{row[1]}' | Count: {row[2]}")
        except Exception as e:
            logger.warning(f"⚠️ Debug recent query failed: {e}")
        
        query = """
        WITH shortage_metrics AS (
            SELECT 
                COUNT(*) as total_shortages,
                COUNT(DISTINCT company_name) as companies_with_shortages,
                COUNT(DISTINCT therapeutic_category) as affected_categories,
                COUNT(CASE WHEN status = 'Current' THEN 1 END) as current_shortages,
                COUNT(CASE WHEN status IN ('Current', 'To Be Discontinued') THEN 1 END) as active_shortages,
                COUNT(CASE WHEN initial_posting_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as shortages_last_30_days
            FROM drug_shortage_data
        ),
        enforcement_metrics AS (
            SELECT 
                COUNT(*) as total_enforcements,
                COUNT(DISTINCT recalling_firm) as companies_with_enforcements,
                COUNT(CASE WHEN classification = 'Class I' THEN 1 END) as class_i_recalls,
                COUNT(CASE WHEN status = 'Ongoing' THEN 1 END) as ongoing_recalls,
                COUNT(CASE WHEN recall_initiation_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as enforcements_last_30_days
            FROM drug_enforcement_data
        ),
        unique_companies AS (
            SELECT COUNT(DISTINCT company_name) as total_companies_affected
            FROM (
                SELECT DISTINCT company_name FROM drug_shortage_data WHERE company_name IS NOT NULL
                UNION
                SELECT DISTINCT recalling_firm as company_name FROM drug_enforcement_data WHERE recalling_firm IS NOT NULL
            ) combined_companies
        )
        SELECT 
            s.total_shortages,
            s.companies_with_shortages,
            s.affected_categories,
            s.current_shortages,
            s.active_shortages,
            s.shortages_last_30_days,
            e.total_enforcements,
            e.companies_with_enforcements,
            e.class_i_recalls,
            e.ongoing_recalls,
            e.enforcements_last_30_days,
            u.total_companies_affected,
            (s.total_shortages + e.total_enforcements) as total_issues,
            CURRENT_DATE as metrics_date
        FROM shortage_metrics s
        CROSS JOIN enforcement_metrics e
        CROSS JOIN unique_companies u
        """
        
        self.create_table_from_query(
            "dashboard_summary_metrics", 
            query, 
            "High-level summary metrics"
        )
    
    def create_all_datasets(self):
        """Create all dashboard datasets."""
        logger.info("🚀 Starting dashboard dataset creation...")
        
        try:
            # Check if source tables exist
            self.check_source_tables()
            
            # Create all datasets
            self.create_monthly_trends_dataset()
            self.create_company_analysis_dataset()
            self.create_therapeutic_category_analysis_dataset()
            self.create_geographic_analysis_dataset()
            self.create_top_drugs_dataset()
            self.create_shortage_reasons_dataset()
            self.create_recall_severity_dataset()
            self.create_recent_activity_dataset()
            self.create_summary_metrics_dataset()
            
            logger.info("✅ All dashboard datasets created successfully!")
            self.show_dataset_summary()
            
        except Exception as e:
            logger.error(f"❌ Error creating dashboard datasets: {e}")
            raise
    
    def check_source_tables(self):
        """Check if source tables exist and have data."""
        tables = ['drug_shortage_data', 'drug_enforcement_data']
        
        for table in tables:
            query = f"SELECT COUNT(*) as count FROM {table};"
            result = self.execute_sql(query, f"Checking {table}")
            count = result.fetchone()[0]
            
            if count == 0:
                logger.warning(f"⚠️  Table {table} is empty!")
            else:
                logger.info(f"✅ Table {table} has {count} records")
    
    def show_dataset_summary(self):
        """Show summary of created datasets."""
        logger.info("\n📊 DASHBOARD DATASETS SUMMARY")
        logger.info("=" * 50)
        
        dashboard_tables = [
            'dashboard_monthly_trends',
            'dashboard_company_analysis', 
            'dashboard_therapeutic_categories',
            'dashboard_geographic_analysis',
            'dashboard_top_drugs',
            'dashboard_shortage_reasons',
            'dashboard_recall_severity',
            'dashboard_recent_activity',
            'dashboard_summary_metrics'
        ]
        
        for table in dashboard_tables:
            try:
                query = f"SELECT COUNT(*) as count FROM {table};"
                result = self.execute_sql(query)
                count = result.fetchone()[0]
                logger.info(f"📋 {table}: {count} records")
            except Exception as e:
                logger.error(f"❌ Error checking {table}: {e}")


def main():
    """Main function to create all dashboard datasets."""
    try:
        # Check database credentials
        if not DB_CONFIG['user'] or not DB_CONFIG['password'] or not DB_CONFIG['host']:
            logger.error("Database credentials not found in .env file")
            return
        
        # Create dashboard datasets
        creator = DashboardDatasetCreator()
        creator.create_all_datasets()
        
        logger.info("🎉 Dashboard datasets are ready for visualization!")
        
    except Exception as e:
        logger.error(f"❌ Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main() 