#!/usr/bin/env python3
"""
Simple script to run the drug shortage prediction ML pipeline.
This provides an easy way to get started with machine learning analysis.
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append('.')

try:
    from ml_shortage_prediction import DrugShortagePredictor
    from drug_data_utils import check_database_credentials, logger
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    # Check database credentials
    if not check_database_credentials():
        print("❌ Database credentials not found!")
        print("Please create a .env file with database credentials")
        return False
    
    # Check required libraries
    required_packages = ['sklearn', 'xgboost', 'matplotlib', 'seaborn']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install missing packages:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ All prerequisites met!")
    return True

def run_basic_analysis():
    """Run basic ML analysis"""
    print("\n🚀 Running Drug Shortage Prediction Analysis")
    print("=" * 60)
    
    try:
        # Initialize predictor
        predictor = DrugShortagePredictor()
        
        # Run full pipeline
        results, predictions = predictor.run_full_pipeline()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if predictions is not None:
            predictions.to_csv(f'shortage_predictions_{timestamp}.csv', index=False)
            print(f"\n💾 Predictions saved to: shortage_predictions_{timestamp}.csv")
        
        return results, predictions
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        print(f"❌ Analysis failed: {e}")
        return None, None

def run_specific_drug_analysis(drug_name):
    """Run analysis for a specific drug"""
    print(f"\n🔍 Analyzing shortage risk for: {drug_name}")
    print("=" * 60)
    
    try:
        predictor = DrugShortagePredictor()
        
        # Load data and prepare models
        predictor.load_data()
        predictor.create_target_variable()
        predictor.engineer_features()
        predictor.prepare_for_modeling()
        predictor.train_models()
        
        # Get predictions for specific drug
        predictions = predictor.predict_shortage_risk(drug_name=drug_name, top_n=1)
        
        if predictions is not None and len(predictions) > 0:
            result = predictions.iloc[0]
            print(f"\n📊 Analysis Results for {drug_name}:")
            print(f"  Company: {result['company_name']}")
            print(f"  Shortage Probability: {result['shortage_probability']:.3f}")
            print(f"  Risk Level: {result['risk_level']}")
        else:
            print(f"❌ No data found for drug: {drug_name}")
        
        return predictions
        
    except Exception as e:
        logger.error(f"Error during specific drug analysis: {e}")
        print(f"❌ Analysis failed: {e}")
        return None

def run_company_analysis(company_name):
    """Run analysis for a specific company"""
    print(f"\n🏢 Analyzing shortage risk for company: {company_name}")
    print("=" * 60)
    
    try:
        predictor = DrugShortagePredictor()
        
        # Load data and prepare models
        predictor.load_data()
        predictor.create_target_variable()
        predictor.engineer_features()
        predictor.prepare_for_modeling()
        predictor.train_models()
        
        # Get predictions for specific company
        predictions = predictor.predict_shortage_risk(company_name=company_name, top_n=10)
        
        if predictions is not None and len(predictions) > 0:
            print(f"\n📊 Top 10 At-Risk Drugs for {company_name}:")
            for i, (_, row) in enumerate(predictions.head(10).iterrows(), 1):
                print(f"  {i}. {row['drug_name']} - Probability: {row['shortage_probability']:.3f} ({row['risk_level']})")
        else:
            print(f"❌ No data found for company: {company_name}")
        
        return predictions
        
    except Exception as e:
        logger.error(f"Error during company analysis: {e}")
        print(f"❌ Analysis failed: {e}")
        return None

def show_help():
    """Show usage help"""
    print("\n📚 Drug Shortage Prediction ML Pipeline")
    print("=" * 50)
    print("Usage: python run_ml_analysis.py [options]")
    print("\nOptions:")
    print("  (no args)           - Run full analysis pipeline")
    print("  --drug <name>       - Analyze specific drug")
    print("  --company <name>    - Analyze specific company")
    print("  --help             - Show this help message")
    print("\nExamples:")
    print("  python run_ml_analysis.py")
    print("  python run_ml_analysis.py --drug 'Amoxicillin'")
    print("  python run_ml_analysis.py --company 'Pfizer'")
    print("\nPrerequisites:")
    print("  - Database credentials in .env file")
    print("  - Required Python packages (pip install -r requirements.txt)")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Drug Shortage Prediction ML Pipeline')
    parser.add_argument('--drug', type=str, help='Analyze specific drug')
    parser.add_argument('--company', type=str, help='Analyze specific company')
    parser.add_argument('--help-full', action='store_true', help='Show detailed help')
    
    args = parser.parse_args()
    
    if args.help_full:
        show_help()
        return
    
    # Check prerequisites
    if not check_prerequisites():
        return
    
    # Run analysis based on arguments
    if args.drug:
        run_specific_drug_analysis(args.drug)
    elif args.company:
        run_company_analysis(args.company)
    else:
        run_basic_analysis()

if __name__ == "__main__":
    main() 