#!/usr/bin/env python3
"""
Machine Learning Pipeline for Drug Shortage Prediction
=====================================================

This script implements a complete ML pipeline to predict drug shortages using:
- Feature engineering from historical shortage and enforcement data
- Multiple ML algorithms (Logistic Regression, Random Forest, XGBoost)
- Model evaluation and validation
- Predictive scoring for future shortages

Features engineered include:
- Historical shortage frequency by drug/manufacturer
- Time between enforcement actions and shortages
- Seasonal patterns and trends
- Company risk profiles
- Therapeutic category risk scores
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ML libraries
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
import xgboost as xgb

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns

# Custom imports
from extract_data_for_analysis import extract_both_datasets, get_data_summary
from drug_data_utils import logger

class DrugShortagePredictor:
    """
    Complete ML pipeline for drug shortage prediction
    """
    
    def __init__(self):
        self.shortage_df = None
        self.enforcement_df = None
        self.features_df = None
        self.models = {}
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
    def load_data(self):
        """Load data from PostgreSQL database"""
        logger.info("Loading data from database...")
        self.shortage_df, self.enforcement_df = extract_both_datasets()
        
        # Convert date columns
        self.shortage_df['initial_posting_date'] = pd.to_datetime(self.shortage_df['initial_posting_date'])
        self.shortage_df['update_date'] = pd.to_datetime(self.shortage_df['update_date'])
        self.enforcement_df['recall_initiation_date'] = pd.to_datetime(self.enforcement_df['recall_initiation_date'])
        
        logger.info(f"Loaded {len(self.shortage_df)} shortage records and {len(self.enforcement_df)} enforcement records")
        
    def create_target_variable(self):
        """
        Create target variable for shortage prediction.
        We'll predict if a drug will have a shortage in the next 90 days.
        """
        logger.info("Creating target variable...")
        
        # Get unique drugs and their shortage history
        drug_shortage_history = []
        
        for drug_name in self.shortage_df['generic_name'].dropna().unique():
            drug_data = self.shortage_df[self.shortage_df['generic_name'] == drug_name].copy()
            drug_data = drug_data.sort_values('initial_posting_date')
            
            # Create records for each drug with time-based features
            for i in range(len(drug_data)):
                record = drug_data.iloc[i]
                
                # Features up to this point in time
                historical_data = drug_data.iloc[:i] if i > 0 else pd.DataFrame()
                
                # Target: Is there a shortage in the next 90 days?
                future_date = record['initial_posting_date'] + timedelta(days=90)
                future_shortages = drug_data[drug_data['initial_posting_date'] > record['initial_posting_date']]
                future_shortages = future_shortages[future_shortages['initial_posting_date'] <= future_date]
                
                has_future_shortage = len(future_shortages) > 0
                
                drug_shortage_history.append({
                    'drug_name': drug_name,
                    'company_name': record['company_name'],
                    'therapeutic_category': record['therapeutic_category'],
                    'reference_date': record['initial_posting_date'],
                    'current_shortage': True,  # This record represents a shortage
                    'future_shortage': has_future_shortage,
                    'historical_shortage_count': len(historical_data),
                    'days_since_last_shortage': (record['initial_posting_date'] - historical_data['initial_posting_date'].max()).days if len(historical_data) > 0 else 999
                })
        
        # Also create records for drugs that haven't had shortages (negative examples)
        # This is important for a balanced dataset
        all_drugs = set(self.shortage_df['generic_name'].dropna().unique())
        shortage_drugs = set([r['drug_name'] for r in drug_shortage_history])
        
        # Add non-shortage examples (drugs that appear in other contexts)
        for drug_name in all_drugs:
            if drug_name not in shortage_drugs:
                # Create a few negative examples for this drug
                for _ in range(3):  # Create 3 negative examples per non-shortage drug
                    random_date = datetime.now() - timedelta(days=np.random.randint(30, 1000))
                    drug_shortage_history.append({
                        'drug_name': drug_name,
                        'company_name': 'Unknown',
                        'therapeutic_category': 'Unknown',
                        'reference_date': random_date,
                        'current_shortage': False,
                        'future_shortage': False,
                        'historical_shortage_count': 0,
                        'days_since_last_shortage': 999
                    })
        
        self.target_df = pd.DataFrame(drug_shortage_history)
        logger.info(f"Created {len(self.target_df)} target records")
        
    def engineer_features(self):
        """
        Engineer features for machine learning model
        """
        logger.info("Engineering features...")
        
        features_list = []
        
        for _, row in self.target_df.iterrows():
            drug_name = row['drug_name']
            company_name = row['company_name']
            reference_date = row['reference_date']
            
            # Historical shortage features
            historical_shortages = self.shortage_df[
                (self.shortage_df['generic_name'] == drug_name) & 
                (self.shortage_df['initial_posting_date'] < reference_date)
            ]
            
            # Company-level features
            company_shortages = self.shortage_df[
                (self.shortage_df['company_name'] == company_name) & 
                (self.shortage_df['initial_posting_date'] < reference_date)
            ]
            
            # Enforcement history features
            company_enforcements = self.enforcement_df[
                (self.enforcement_df['recalling_firm'].str.contains(company_name[:10], case=False, na=False)) & 
                (self.enforcement_df['recall_initiation_date'] < reference_date)
            ]
            
            # Time-based features
            days_since_epoch = (reference_date - datetime(2020, 1, 1)).days
            month = reference_date.month
            quarter = (reference_date.month - 1) // 3 + 1
            
            # Feature engineering
            features = {
                # Target variables
                'drug_name': drug_name,
                'company_name': company_name,
                'reference_date': reference_date,
                'target': row['future_shortage'],
                
                # Historical shortage features
                'historical_shortage_count': len(historical_shortages),
                'days_since_last_shortage': row['days_since_last_shortage'],
                'avg_shortage_duration': historical_shortages['initial_posting_date'].diff().dt.days.mean() if len(historical_shortages) > 1 else 0,
                
                # Company risk features
                'company_shortage_count': len(company_shortages),
                'company_shortage_rate': len(company_shortages) / max(1, days_since_epoch / 365),
                'company_unique_drugs_affected': company_shortages['generic_name'].nunique(),
                
                # Enforcement features
                'recent_enforcements_30d': len(company_enforcements[company_enforcements['recall_initiation_date'] > reference_date - timedelta(days=30)]),
                'recent_enforcements_90d': len(company_enforcements[company_enforcements['recall_initiation_date'] > reference_date - timedelta(days=90)]),
                'recent_enforcements_365d': len(company_enforcements[company_enforcements['recall_initiation_date'] > reference_date - timedelta(days=365)]),
                'class_i_recalls': len(company_enforcements[company_enforcements['classification'] == 'Class I']),
                'days_since_last_enforcement': (reference_date - company_enforcements['recall_initiation_date'].max()).days if len(company_enforcements) > 0 else 999,
                
                # Therapeutic category features
                'therapeutic_category': row['therapeutic_category'],
                
                # Seasonal features
                'month': month,
                'quarter': quarter,
                'is_q4': 1 if quarter == 4 else 0,
                
                # Time trend features
                'days_since_epoch': days_since_epoch,
                'year': reference_date.year,
                
                # Drug-specific features
                'drug_name_length': len(drug_name) if drug_name else 0,
                'is_generic': 1 if (drug_name and any(word in drug_name.lower() for word in ['generic', 'tablet', 'capsule'])) else 0,
            }
            
            features_list.append(features)
        
        self.features_df = pd.DataFrame(features_list)
        
        # Handle missing values
        self.features_df = self.features_df.fillna(0)
        
        logger.info(f"Engineered {len(self.features_df.columns)} features for {len(self.features_df)} records")
        
    def prepare_for_modeling(self):
        """
        Prepare features for machine learning modeling
        """
        logger.info("Preparing features for modeling...")
        
        # Encode categorical variables
        categorical_cols = ['therapeutic_category', 'drug_name', 'company_name']
        
        for col in categorical_cols:
            if col in self.features_df.columns:
                le = LabelEncoder()
                # Handle unknown categories
                self.features_df[col] = self.features_df[col].astype(str)
                self.features_df[f'{col}_encoded'] = le.fit_transform(self.features_df[col])
                self.label_encoders[col] = le
        
        # Select features for modeling
        feature_columns = [
            'historical_shortage_count', 'days_since_last_shortage', 'avg_shortage_duration',
            'company_shortage_count', 'company_shortage_rate', 'company_unique_drugs_affected',
            'recent_enforcements_30d', 'recent_enforcements_90d', 'recent_enforcements_365d',
            'class_i_recalls', 'days_since_last_enforcement',
            'month', 'quarter', 'is_q4', 'days_since_epoch', 'year',
            'drug_name_length', 'is_generic',
            'therapeutic_category_encoded', 'drug_name_encoded', 'company_name_encoded'
        ]
        
        # Filter to existing columns
        feature_columns = [col for col in feature_columns if col in self.features_df.columns]
        
        self.X = self.features_df[feature_columns]
        self.y = self.features_df['target'].astype(int)
        
        # Handle infinite values
        self.X = self.X.replace([np.inf, -np.inf], 0)
        
        logger.info(f"Prepared {self.X.shape[1]} features for {self.X.shape[0]} samples")
        logger.info(f"Target distribution: {self.y.value_counts().to_dict()}")
        
    def train_models(self):
        """
        Train multiple ML models
        """
        logger.info("Training machine learning models...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42, stratify=self.y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Store test data for evaluation
        self.X_test_scaled = X_test_scaled
        self.X_test = X_test
        self.y_test = y_test
        
        # 1. Logistic Regression
        logger.info("Training Logistic Regression...")
        lr_model = LogisticRegression(random_state=42, max_iter=1000)
        lr_model.fit(X_train_scaled, y_train)
        self.models['logistic_regression'] = lr_model
        
        # 2. Random Forest
        logger.info("Training Random Forest...")
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        rf_model.fit(X_train, y_train)  # RF doesn't need scaling
        self.models['random_forest'] = rf_model
        
        # 3. XGBoost
        logger.info("Training XGBoost...")
        xgb_model = xgb.XGBClassifier(random_state=42, eval_metric='logloss')
        xgb_model.fit(X_train, y_train)
        self.models['xgboost'] = xgb_model
        
        logger.info("Model training completed")
        
    def evaluate_models(self):
        """
        Evaluate all trained models
        """
        logger.info("Evaluating models...")
        
        results = {}
        
        for model_name, model in self.models.items():
            logger.info(f"Evaluating {model_name}...")
            
            # Make predictions
            if model_name == 'logistic_regression':
                y_pred = model.predict(self.X_test_scaled)
                y_pred_proba = model.predict_proba(self.X_test_scaled)[:, 1]
            else:
                # For tree-based models, use original X_test (not scaled)
                y_pred = model.predict(self.X_test)
                y_pred_proba = model.predict_proba(self.X_test)[:, 1]
            
            # Calculate metrics
            auc_score = roc_auc_score(self.y_test, y_pred_proba)
            
            results[model_name] = {
                'auc_score': auc_score,
                'classification_report': classification_report(self.y_test, y_pred),
                'confusion_matrix': confusion_matrix(self.y_test, y_pred)
            }
            
            print(f"\n{model_name.upper()} Results:")
            print(f"AUC Score: {auc_score:.4f}")
            print(f"Classification Report:\n{results[model_name]['classification_report']}")
            print(f"Confusion Matrix:\n{results[model_name]['confusion_matrix']}")
        
        return results
        
    def get_feature_importance(self):
        """
        Get feature importance from tree-based models
        """
        logger.info("Analyzing feature importance...")
        
        # Random Forest feature importance
        if 'random_forest' in self.models:
            rf_importance = pd.DataFrame({
                'feature': self.X.columns,
                'importance': self.models['random_forest'].feature_importances_
            }).sort_values('importance', ascending=False)
            
            print("\nTop 10 Most Important Features (Random Forest):")
            print(rf_importance.head(10))
            
        # XGBoost feature importance
        if 'xgboost' in self.models:
            xgb_importance = pd.DataFrame({
                'feature': self.X.columns,
                'importance': self.models['xgboost'].feature_importances_
            }).sort_values('importance', ascending=False)
            
            print("\nTop 10 Most Important Features (XGBoost):")
            print(xgb_importance.head(10))
            
        return rf_importance if 'random_forest' in self.models else None
        
    def predict_shortage_risk(self, drug_name=None, company_name=None, top_n=20):
        """
        Predict shortage risk for current drugs
        """
        logger.info("Predicting shortage risk...")
        
        # Use the best model (let's use XGBoost if available)
        best_model = self.models.get('xgboost', self.models.get('random_forest', self.models.get('logistic_regression')))
        
        if best_model is None:
            logger.error("No trained models available")
            return None
        
        # Create current predictions
        current_date = datetime.now()
        current_features = []
        
        # Get unique drugs for prediction
        drugs_to_predict = self.features_df['drug_name'].unique()
        
        if drug_name:
            drugs_to_predict = [drug_name]
        
        for drug in drugs_to_predict[:100]:  # Limit to avoid too many predictions
            # Create features for current date
            drug_data = self.shortage_df[self.shortage_df['generic_name'] == drug]
            
            if len(drug_data) == 0:
                continue
                
            company = drug_data['company_name'].iloc[0] if company_name is None else company_name
            
            # Calculate features for current date
            historical_shortages = drug_data[drug_data['initial_posting_date'] < current_date]
            company_shortages = self.shortage_df[
                (self.shortage_df['company_name'] == company) & 
                (self.shortage_df['initial_posting_date'] < current_date)
            ]
            
            features = {
                'drug_name': drug,
                'company_name': company,
                'historical_shortage_count': len(historical_shortages),
                'days_since_last_shortage': (current_date - historical_shortages['initial_posting_date'].max()).days if len(historical_shortages) > 0 else 999,
                'company_shortage_count': len(company_shortages),
                'month': current_date.month,
                'quarter': (current_date.month - 1) // 3 + 1,
                'year': current_date.year,
                'days_since_epoch': (current_date - datetime(2020, 1, 1)).days,
            }
            
            current_features.append(features)
        
        if not current_features:
            logger.warning("No features created for prediction")
            return None
        
        # Create prediction DataFrame
        pred_df = pd.DataFrame(current_features)
        
        # Encode categorical variables
        for col in ['drug_name', 'company_name']:
            if col in pred_df.columns and col in self.label_encoders:
                pred_df[f'{col}_encoded'] = pred_df[col].map(
                    dict(zip(self.label_encoders[col].classes_, self.label_encoders[col].transform(self.label_encoders[col].classes_)))
                ).fillna(-1)
        
        # Fill missing features with defaults
        for col in self.X.columns:
            if col not in pred_df.columns:
                pred_df[col] = 0
        
        # Select and order features
        pred_features = pred_df[self.X.columns].fillna(0)
        
        # Make predictions
        shortage_probabilities = best_model.predict_proba(pred_features)[:, 1]
        
        # Create results
        results = pd.DataFrame({
            'drug_name': pred_df['drug_name'],
            'company_name': pred_df['company_name'],
            'shortage_probability': shortage_probabilities,
            'risk_level': pd.cut(shortage_probabilities, bins=[0, 0.3, 0.7, 1.0], labels=['Low', 'Medium', 'High'])
        }).sort_values('shortage_probability', ascending=False)
        
        print(f"\nTop {top_n} Drugs at Risk of Shortage:")
        print(results.head(top_n))
        
        return results
        
    def run_full_pipeline(self):
        """
        Run the complete ML pipeline
        """
        print("🚀 Starting Drug Shortage Prediction Pipeline")
        print("=" * 60)
        
        # Step 1: Load data
        self.load_data()
        
        # Step 2: Create target variable
        self.create_target_variable()
        
        # Step 3: Engineer features
        self.engineer_features()
        
        # Step 4: Prepare for modeling
        self.prepare_for_modeling()
        
        # Step 5: Train models
        self.train_models()
        
        # Step 6: Evaluate models
        results = self.evaluate_models()
        
        # Step 7: Feature importance
        self.get_feature_importance()
        
        # Step 8: Make predictions
        predictions = self.predict_shortage_risk()
        
        print("\n✅ Pipeline completed successfully!")
        
        return results, predictions

if __name__ == "__main__":
    # Run the complete pipeline
    predictor = DrugShortagePredictor()
    results, predictions = predictor.run_full_pipeline() 