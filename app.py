#!/usr/bin/env python3
"""
Flask API Backend for Drug Shortage Prediction Dashboard
========================================================

This Flask application serves the ML predictions and data for the D3.js frontend.
Provides RESTful API endpoints for interactive data visualization.
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import os
import sys

# Add current directory to path
sys.path.append('.')

try:
    from ml_shortage_prediction import DrugShortagePredictor
    from extract_data_for_analysis import extract_both_datasets, get_data_summary
    from drug_data_utils import check_database_credentials, logger
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

app = Flask(__name__)
CORS(app)

# Global variables to cache data
predictor = None
shortage_data = None
enforcement_data = None
predictions = None
model_results = None

def initialize_predictor():
    """Initialize the ML predictor with trained models"""
    global predictor, predictions, model_results
    
    if predictor is None:
        logger.info("Initializing ML predictor...")
        predictor = DrugShortagePredictor()
        
        # Load data and train models
        predictor.load_data()
        predictor.create_target_variable()
        predictor.engineer_features()
        predictor.prepare_for_modeling()
        predictor.train_models()
        
        # Get predictions and model results
        model_results = predictor.evaluate_models()
        predictions = predictor.predict_shortage_risk(top_n=100)
        
        logger.info("ML predictor initialized successfully")
    
    return predictor

def load_data():
    """Load and cache the dataset"""
    global shortage_data, enforcement_data
    
    if shortage_data is None or enforcement_data is None:
        logger.info("Loading data...")
        shortage_data, enforcement_data = extract_both_datasets()
        
        # Convert dates
        shortage_data['initial_posting_date'] = pd.to_datetime(shortage_data['initial_posting_date'])
        enforcement_data['recall_initiation_date'] = pd.to_datetime(enforcement_data['recall_initiation_date'])
    
    return shortage_data, enforcement_data

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/summary')
def api_summary():
    """Get data summary statistics"""
    try:
        summary = get_data_summary()
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/predictions')
def api_predictions():
    """Get ML predictions"""
    try:
        initialize_predictor()
        
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        risk_level = request.args.get('risk_level', None)
        company = request.args.get('company', None)
        
        # Filter predictions
        filtered_predictions = predictions.copy()
        
        if risk_level:
            filtered_predictions = filtered_predictions[filtered_predictions['risk_level'] == risk_level]
        
        if company:
            filtered_predictions = filtered_predictions[filtered_predictions['company_name'].str.contains(company, case=False, na=False)]
        
        # Limit results
        result_data = filtered_predictions.head(limit)
        
        # Convert to JSON-serializable format
        result_dict = result_data.to_dict('records')
        
        return jsonify({
            'predictions': result_dict,
            'total_count': len(filtered_predictions),
            'returned_count': len(result_data)
        })
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/model_performance')
def api_model_performance():
    """Get model performance metrics"""
    try:
        initialize_predictor()
        
        # Format model results for JSON
        performance_data = {}
        for model_name, results in model_results.items():
            performance_data[model_name] = {
                'auc_score': float(results['auc_score']),
                'confusion_matrix': results['confusion_matrix'].tolist()
            }
        
        return jsonify(performance_data)
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/feature_importance')
def api_feature_importance():
    """Get feature importance data"""
    try:
        initialize_predictor()
        
        # Get feature importance from Random Forest
        if 'random_forest' in predictor.models:
            importance_df = pd.DataFrame({
                'feature': predictor.X.columns,
                'importance': predictor.models['random_forest'].feature_importances_
            }).sort_values('importance', ascending=False)
            
            return jsonify(importance_df.head(15).to_dict('records'))
        else:
            return jsonify({'error': 'Random Forest model not available'}), 500
    except Exception as e:
        logger.error(f"Error getting feature importance: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/shortage_timeline')
def api_shortage_timeline():
    """Get shortage timeline data"""
    try:
        shortage_data, _ = load_data()
        
        # Group by month
        timeline_data = shortage_data.groupby(shortage_data['initial_posting_date'].dt.to_period('M')).size().reset_index()
        timeline_data.columns = ['month', 'count']
        timeline_data['month'] = timeline_data['month'].astype(str)
        
        return jsonify(timeline_data.to_dict('records'))
    except Exception as e:
        logger.error(f"Error getting shortage timeline: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/enforcement_timeline')
def api_enforcement_timeline():
    """Get enforcement timeline data"""
    try:
        _, enforcement_data = load_data()
        
        # Group by month
        timeline_data = enforcement_data.groupby(enforcement_data['recall_initiation_date'].dt.to_period('M')).size().reset_index()
        timeline_data.columns = ['month', 'count']
        timeline_data['month'] = timeline_data['month'].astype(str)
        
        return jsonify(timeline_data.to_dict('records'))
    except Exception as e:
        logger.error(f"Error getting enforcement timeline: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/company_risk')
def api_company_risk():
    """Get company risk analysis"""
    try:
        shortage_data, enforcement_data = load_data()
        
        # Calculate company risk metrics
        company_shortages = shortage_data['company_name'].value_counts().head(20)
        company_enforcements = enforcement_data['recalling_firm'].value_counts().head(20)
        
        # Create combined risk score
        risk_data = []
        for company in company_shortages.index:
            shortages = company_shortages.get(company, 0)
            enforcements = company_enforcements.get(company, 0)
            risk_score = shortages * 0.7 + enforcements * 0.3  # Weighted score
            
            risk_data.append({
                'company': company,
                'shortages': int(shortages),
                'enforcements': int(enforcements),
                'risk_score': float(risk_score)
            })
        
        # Sort by risk score
        risk_data.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return jsonify(risk_data[:15])
    except Exception as e:
        logger.error(f"Error getting company risk: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/drug_categories')
def api_drug_categories():
    """Get drug categories risk analysis"""
    try:
        shortage_data, _ = load_data()
        
        # Group by therapeutic category
        category_data = shortage_data.groupby('therapeutic_category').size().reset_index()
        category_data.columns = ['category', 'count']
        category_data = category_data.sort_values('count', ascending=False).head(10)
        
        return jsonify(category_data.to_dict('records'))
    except Exception as e:
        logger.error(f"Error getting drug categories: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk_distribution')
def api_risk_distribution():
    """Get risk level distribution"""
    try:
        initialize_predictor()
        
        # Get risk level distribution
        risk_dist = predictions['risk_level'].value_counts().to_dict()
        
        # Convert to list format for D3
        risk_data = [
            {'risk_level': level, 'count': int(count)} 
            for level, count in risk_dist.items()
        ]
        
        return jsonify(risk_data)
    except Exception as e:
        logger.error(f"Error getting risk distribution: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search_drug')
def api_search_drug():
    """Search for specific drug predictions"""
    try:
        drug_name = request.args.get('drug_name', '')
        
        if not drug_name:
            return jsonify({'error': 'Drug name required'}), 400
        
        initialize_predictor()
        
        # Get predictions for specific drug
        specific_predictions = predictor.predict_shortage_risk(drug_name=drug_name, top_n=10)
        
        if specific_predictions is not None and len(specific_predictions) > 0:
            return jsonify(specific_predictions.to_dict('records'))
        else:
            return jsonify({'message': f'No predictions found for {drug_name}'}), 404
    except Exception as e:
        logger.error(f"Error searching drug: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database_connected': check_database_credentials()
    })

if __name__ == '__main__':
    # Check prerequisites
    if not check_database_credentials():
        print("❌ Database credentials not found!")
        print("Please create a .env file with database credentials")
        sys.exit(1)
    
    print("🚀 Starting Drug Shortage Prediction Dashboard")
    print("=" * 50)
    print("Dashboard will be available at: http://localhost:5000")
    print("API endpoints available at: http://localhost:5000/api/")
    
    app.run(debug=True, port=5000) 