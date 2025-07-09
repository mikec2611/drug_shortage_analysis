#!/usr/bin/env python3
"""
Flask web application for Drug Shortage Analysis Dashboard.
Provides interactive visualizations of drug shortage and enforcement data.
"""

from flask import Flask, render_template, jsonify, request
import os
import json
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text
from drug_data_utils import DB_CONFIG, logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Database connection
engine = create_engine(f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")

def execute_query(query):
    """Execute a database query and return results as a list of dictionaries."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Database query error: {e}")
        return []

def format_date(date_obj):
    """Format date objects for JSON serialization."""
    if date_obj:
        return date_obj.strftime('%Y-%m-%d')
    return None

def serialize_data(data):
    """Convert data to JSON-serializable format."""
    for record in data:
        for key, value in record.items():
            if hasattr(value, 'date'):  # datetime.date objects
                record[key] = format_date(value)
            elif isinstance(value, datetime):
                record[key] = value.isoformat()
    return data

# Routes
@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')

@app.route('/api/summary_metrics')
def api_summary_metrics():
    """API endpoint for summary metrics."""
    query = """
    SELECT 
        total_shortages,
        companies_with_shortages,
        affected_categories,
        current_shortages,
        active_shortages,
        shortages_last_30_days,
        total_enforcements,
        companies_with_enforcements,
        class_i_recalls,
        ongoing_recalls,
        enforcements_last_30_days,
        total_companies_affected,
        total_issues,
        metrics_date
    FROM dashboard_summary_metrics 
    LIMIT 1;
    """
    data = execute_query(query)
    return jsonify(serialize_data(data)[0] if data else {})

@app.route('/api/companies')
def api_companies():
    """API endpoint for list of companies."""
    query = """
    SELECT DISTINCT company_name as name, 'shortage' as type
    FROM drug_shortage_data 
    WHERE company_name IS NOT NULL
    UNION
    SELECT DISTINCT recalling_firm as name, 'enforcement' as type
    FROM drug_enforcement_data 
    WHERE recalling_firm IS NOT NULL
    ORDER BY name;
    """
    try:
        data = execute_query(query)
        if not data:
            return jsonify([])
        
        # Extract unique company names safely (data is list of dicts, not tuples)
        companies = []
        for row in data:
            if row and 'name' in row and row['name']:  # Check if row exists and has name
                companies.append(row['name'])
        
        # Remove duplicates and sort
        unique_companies = sorted(list(set(companies)))
        return jsonify(unique_companies)
        
    except Exception as e:
        logger.error(f"Error in companies endpoint: {e}")
        return jsonify({'error': 'Failed to load companies'}), 500

@app.route('/api/monthly_trends')
def api_monthly_trends():
    """API endpoint for monthly trends data."""
    company = request.args.get('company')
    
    if company:
        query = f"""
        WITH shortage_monthly AS (
            SELECT 
                DATE_TRUNC('month', initial_posting_date) as month,
                COUNT(*) as shortage_count,
                COUNT(DISTINCT company_name) as companies_with_shortages,
                COUNT(DISTINCT therapeutic_category) as affected_categories
            FROM drug_shortage_data 
            WHERE initial_posting_date IS NOT NULL AND company_name = '{company}'
            GROUP BY DATE_TRUNC('month', initial_posting_date)
        ),
        enforcement_monthly AS (
            SELECT 
                DATE_TRUNC('month', recall_initiation_date) as month,
                COUNT(*) as enforcement_count,
                COUNT(DISTINCT recalling_firm) as companies_with_enforcements,
                COUNT(DISTINCT classification) as enforcement_types
            FROM drug_enforcement_data 
            WHERE recall_initiation_date IS NOT NULL AND recalling_firm = '{company}'
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
        ORDER BY month;
        """
    else:
        query = "SELECT * FROM dashboard_monthly_trends ORDER BY month;"
    
    data = execute_query(query)
    return jsonify(serialize_data(data))

@app.route('/api/company_analysis')
def api_company_analysis():
    """API endpoint for company analysis data."""
    company = request.args.get('company')
    limit = request.args.get('limit', 15, type=int)
    
    if company:
        query = f"""
        SELECT * FROM dashboard_company_analysis 
        WHERE company_name = '{company}'
        ORDER BY total_issues DESC 
        LIMIT {limit};
        """
    else:
        query = f"""
        SELECT * FROM dashboard_company_analysis 
        ORDER BY total_issues DESC 
        LIMIT {limit};
        """
    
    data = execute_query(query)
    return jsonify(serialize_data(data))

@app.route('/api/therapeutic_categories')
def api_therapeutic_categories():
    """API endpoint for therapeutic categories data."""
    company = request.args.get('company')
    
    if company:
        query = f"""
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
            ) as current_shortage_percentage
        FROM drug_shortage_data 
        WHERE therapeutic_category IS NOT NULL AND company_name = '{company}'
        GROUP BY therapeutic_category
        ORDER BY shortage_count DESC;
        """
    else:
        query = """
        SELECT 
            therapeutic_category,
            shortage_count,
            companies_affected,
            drugs_affected,
            current_shortages,
            current_shortage_percentage
        FROM dashboard_therapeutic_categories 
        ORDER BY shortage_count DESC;
        """
    
    data = execute_query(query)
    return jsonify(serialize_data(data))

@app.route('/api/geographic_analysis')
def api_geographic_analysis():
    """API endpoint for geographic analysis data."""
    query = """
    SELECT 
        state,
        country,
        enforcement_count,
        companies_affected,
        class_i_recalls,
        class_i_percentage,
        ongoing_recalls
    FROM dashboard_geographic_analysis 
    ORDER BY enforcement_count DESC;
    """
    data = execute_query(query)
    return jsonify(serialize_data(data))

@app.route('/api/top_drugs')
def api_top_drugs():
    """API endpoint for top drugs data."""
    company = request.args.get('company')
    limit = request.args.get('limit', 15, type=int)
    
    if company:
        query = f"""
        SELECT 
            generic_name,
            proprietary_name,
            therapeutic_category,
            COUNT(*) as shortage_count,
            COUNT(DISTINCT company_name) as companies_affected,
            COUNT(CASE WHEN status = 'Current' THEN 1 END) as current_shortages,
            CASE 
                WHEN COUNT(CASE WHEN status = 'Current' THEN 1 END) > 0 THEN 'Currently in shortage'
                ELSE 'No current shortage'
            END as current_status
        FROM drug_shortage_data 
        WHERE generic_name IS NOT NULL AND company_name = '{company}'
        GROUP BY generic_name, proprietary_name, therapeutic_category
        ORDER BY shortage_count DESC 
        LIMIT {limit};
        """
    else:
        query = f"""
        SELECT 
            generic_name,
            proprietary_name,
            therapeutic_category,
            shortage_count,
            companies_affected,
            current_shortages,
            current_status
        FROM dashboard_top_drugs 
        ORDER BY shortage_count DESC 
        LIMIT {limit};
        """
    
    data = execute_query(query)
    return jsonify(serialize_data(data))

@app.route('/api/shortage_reasons')
def api_shortage_reasons():
    """API endpoint for shortage reasons data."""
    query = """
    SELECT 
        shortage_reason,
        occurrence_count,
        companies_affected,
        categories_affected,
        current_shortages,
        current_shortage_percentage
    FROM dashboard_shortage_reasons 
    ORDER BY occurrence_count DESC;
    """
    data = execute_query(query)
    return jsonify(serialize_data(data))

@app.route('/api/recall_severity')
def api_recall_severity():
    """API endpoint for recall severity data."""
    query = """
    SELECT 
        classification,
        recall_count,
        companies_affected,
        ongoing_recalls,
        ongoing_percentage
    FROM dashboard_recall_severity 
    ORDER BY 
        CASE classification 
            WHEN 'Class I' THEN 1 
            WHEN 'Class II' THEN 2 
            WHEN 'Class III' THEN 3 
            ELSE 4 
        END;
    """
    data = execute_query(query)
    return jsonify(serialize_data(data))

@app.route('/api/recent_activity')
def api_recent_activity():
    """API endpoint for recent activity data."""
    company = request.args.get('company')
    
    if company:
        query = f"""
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
            AND company_name = '{company}'
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
            AND recalling_firm = '{company}'
        )
        SELECT * FROM recent_shortages
        UNION ALL
        SELECT * FROM recent_enforcements
        ORDER BY issue_date DESC;
        """
    else:
        query = "SELECT * FROM dashboard_recent_activity ORDER BY issue_date DESC;"
    
    data = execute_query(query)
    return jsonify(serialize_data(data))

@app.route('/api/company_detail/<company_name>')
def api_company_detail(company_name):
    """API endpoint for company detail data."""
    # Get company overview
    company_query = f"""
    SELECT * FROM dashboard_company_analysis 
    WHERE company_name = '{company_name}';
    """
    company_data = execute_query(company_query)
    
    # Get recent activity for this company
    activity_query = f"""
    SELECT * FROM dashboard_recent_activity 
    WHERE company = '{company_name}'
    ORDER BY issue_date DESC 
    LIMIT 20;
    """
    activity_data = execute_query(activity_query)
    
    return jsonify({
        'company': serialize_data(company_data),
        'recent_activity': serialize_data(activity_data)
    })

@app.errorhandler(404)
def not_found(error):
    """404 error handler."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler."""
    logger.error(f"Internal server error: {error}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Check database connection
    try:
        test_query = "SELECT 1;"
        execute_query(test_query)
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        exit(1)
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000) 