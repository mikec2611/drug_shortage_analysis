#!/usr/bin/env python3
"""
Example usage patterns for extract_data_for_analysis.py
Shows different ways to extract and filter data for analysis.
"""

from extract_data_for_analysis import (
    extract_both_datasets,
    extract_drug_shortage_data,
    extract_drug_enforcement_data,
    get_data_summary,
    save_datasets_to_csv
)

def example_basic_extraction():
    """Example 1: Basic extraction of both datasets"""
    print("📊 Example 1: Basic extraction of both datasets")
    print("-" * 50)
    
    # Get complete datasets
    shortage_df, enforcement_df = extract_both_datasets()
    
    print(f"Shortage records: {len(shortage_df):,}")
    print(f"Enforcement records: {len(enforcement_df):,}")
    
    return shortage_df, enforcement_df

def example_filtered_extraction():
    """Example 2: Filtered extraction with date ranges"""
    print("\n📊 Example 2: Filtered extraction (2023 data only)")
    print("-" * 50)
    
    # Define filters
    shortage_filters = {
        'date_from': '2023-01-01',
        'date_to': '2023-12-31'
    }
    
    enforcement_filters = {
        'date_from': '2023-01-01',
        'date_to': '2023-12-31'
    }
    
    # Extract filtered data
    shortage_df, enforcement_df = extract_both_datasets(
        shortage_filters=shortage_filters,
        enforcement_filters=enforcement_filters
    )
    
    print(f"2023 Shortage records: {len(shortage_df):,}")
    print(f"2023 Enforcement records: {len(enforcement_df):,}")
    
    return shortage_df, enforcement_df

def example_specific_company_analysis():
    """Example 3: Analysis focused on specific companies"""
    print("\n📊 Example 3: Company-specific analysis")
    print("-" * 50)
    
    # Look for shortages from companies with "Pfizer" in the name
    shortage_df = extract_drug_shortage_data(filters={
        'company_name': 'Pfizer'
    })
    
    print(f"Pfizer-related shortage records: {len(shortage_df):,}")
    
    if len(shortage_df) > 0:
        print("Sample records:")
        print(shortage_df[['proprietary_name', 'company_name', 'status']].head())
    
    return shortage_df

def example_classification_analysis():
    """Example 4: Analysis by enforcement classification"""
    print("\n📊 Example 4: Classification analysis")
    print("-" * 50)
    
    # Get Class I recalls (most serious)
    class_i_recalls = extract_drug_enforcement_data(filters={
        'classification': 'Class I'
    })
    
    print(f"Class I recall records: {len(class_i_recalls):,}")
    
    if len(class_i_recalls) > 0:
        print("Sample Class I recalls:")
        print(class_i_recalls[['product_description', 'recalling_firm', 'reason_for_recall']].head())
    
    return class_i_recalls

def example_state_analysis():
    """Example 5: State-specific enforcement analysis"""
    print("\n📊 Example 5: State-specific analysis")
    print("-" * 50)
    
    # Get recalls from California
    ca_recalls = extract_drug_enforcement_data(filters={
        'state': 'CA'
    })
    
    print(f"California recall records: {len(ca_recalls):,}")
    
    if len(ca_recalls) > 0:
        print("Sample California recalls:")
        print(ca_recalls[['recalling_firm', 'city', 'product_description']].head())
    
    return ca_recalls

def example_recent_data_analysis():
    """Example 6: Recent data analysis (last 6 months)"""
    print("\n📊 Example 6: Recent data analysis")
    print("-" * 50)
    
    # Get recent data (adjust dates as needed)
    recent_filters = {
        'date_from': '2024-01-01'  # Adjust based on current date
    }
    
    recent_shortages = extract_drug_shortage_data(filters=recent_filters)
    recent_enforcements = extract_drug_enforcement_data(filters=recent_filters)
    
    print(f"Recent shortage records: {len(recent_shortages):,}")
    print(f"Recent enforcement records: {len(recent_enforcements):,}")
    
    return recent_shortages, recent_enforcements

def example_combined_analysis():
    """Example 7: Combined analysis with data summary"""
    print("\n📊 Example 7: Combined analysis with summary")
    print("-" * 50)
    
    # Get data summary first
    summary = get_data_summary()
    
    print("Database Summary:")
    print(f"  Shortage records: {summary['shortage_data']['total_records']:,}")
    print(f"  Enforcement records: {summary['enforcement_data']['total_records']:,}")
    
    # Extract both datasets
    shortage_df, enforcement_df = extract_both_datasets()
    
    # Basic analysis
    print(f"\nBasic Analysis:")
    print(f"  Top 5 companies by shortage count:")
    if len(shortage_df) > 0:
        company_counts = shortage_df['company_name'].value_counts().head()
        for company, count in company_counts.items():
            print(f"    {company}: {count}")
    
    print(f"\n  Top 5 states by enforcement count:")
    if len(enforcement_df) > 0:
        state_counts = enforcement_df['state'].value_counts().head()
        for state, count in state_counts.items():
            print(f"    {state}: {count}")
    
    return shortage_df, enforcement_df

def example_save_for_analysis():
    """Example 8: Extract and save datasets for external analysis"""
    print("\n📊 Example 8: Save datasets for external analysis")
    print("-" * 50)
    
    # Extract both datasets
    shortage_df, enforcement_df = extract_both_datasets()
    
    # Save to CSV files
    save_datasets_to_csv(
        shortage_df, 
        enforcement_df,
        shortage_filename="shortage_data_for_analysis.csv",
        enforcement_filename="enforcement_data_for_analysis.csv"
    )
    
    print("✅ Datasets saved for external analysis!")
    
    return shortage_df, enforcement_df

if __name__ == "__main__":
    print("🔍 Drug Data Analysis Examples")
    print("=" * 60)
    
    # Run examples (uncomment the ones you want to try)
    
    # Basic extraction
    example_basic_extraction()
    
    # Filtered by date
    # example_filtered_extraction()
    
    # Company analysis
    # example_specific_company_analysis()
    
    # Classification analysis  
    # example_classification_analysis()
    
    # State analysis
    # example_state_analysis()
    
    # Recent data
    # example_recent_data_analysis()
    
    # Combined analysis
    # example_combined_analysis()
    
    # Save for analysis
    # example_save_for_analysis()
    
    print("\n✅ Examples completed!")
    print("Uncomment other examples in the script to try different analysis patterns.") 