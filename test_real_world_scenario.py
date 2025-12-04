"""
Real-world scenario: Extract climate data for health research

This test demonstrates extracting multiple climate variables for a health study
analyzing the relationship between weather conditions and disease outcomes.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.climate_utils import ClimateDataExtractor
import pandas as pd

def extract_climate_data_for_health_study():
    """
    Real-world scenario: Extract climate data for a malaria/dengue study in Johannesburg

    Research question: How do temperature, precipitation, and humidity affect
    vector-borne disease transmission?
    """
    print("="*80)
    print("REAL-WORLD SCENARIO: Climate Data for Disease Surveillance")
    print("="*80)

    # Initialize
    extractor = ClimateDataExtractor(project_id='joburg-hvi')

    # Study location: Soweto, Johannesburg
    location_name = "Soweto, Johannesburg"
    lat = -26.2678
    lon = 27.8607

    # Study period: Full summer season (Dec-Feb) when disease risk is highest
    start_date = "2023-12-01"
    end_date = "2024-02-29"

    print(f"\nStudy Location: {location_name}")
    print(f"Coordinates: {lat}, {lon}")
    print(f"Study Period: {start_date} to {end_date}")
    print(f"Duration: ~90 days (summer season)")

    # Variables relevant to vector-borne disease transmission
    variables = [
        'temperature',      # Affects mosquito breeding and disease development
        'precipitation',    # Creates breeding sites
        'humidity'          # Affects mosquito survival
    ]

    print(f"\nExtracting variables: {', '.join(variables)}")
    print("Rationale:")
    print("  - Temperature: Affects mosquito metabolism and pathogen development")
    print("  - Precipitation: Creates standing water breeding sites")
    print("  - Humidity: Influences mosquito survival and biting behavior")

    # Create geometry
    geometry = extractor.create_study_area(lat, lon, buffer_km=10)
    point = extractor.create_point(lat, lon)

    # Extract data
    print("\nExtracting climate data from Google Earth Engine...")
    df = extractor.extract_climate_data(
        geometry=geometry,
        point=point,
        start_date=start_date,
        end_date=end_date,
        variables=variables
    )

    print(f"\nSuccessfully extracted {len(df)} daily records")
    print(f"Variables: {list(df.columns)}")

    # Calculate summary statistics
    print("\n" + "="*80)
    print("CLIMATE SUMMARY FOR STUDY PERIOD")
    print("="*80)

    # Temperature analysis
    print("\nTEMPERATURE:")
    print(f"  Mean daily maximum: {df['tmax_celsius'].mean():.1f}°C")
    print(f"  Range: {df['tmax_celsius'].min():.1f}°C to {df['tmax_celsius'].max():.1f}°C")
    print(f"  Days with max temp > 30°C: {(df['tmax_celsius'] > 30).sum()}")
    print(f"  Days with max temp > 35°C: {(df['tmax_celsius'] > 35).sum()}")

    # Precipitation analysis
    print("\nPRECIPITATION:")
    print(f"  Total rainfall: {df['precipitation_mm'].sum():.1f} mm")
    print(f"  Mean daily rainfall: {df['precipitation_mm'].mean():.1f} mm")
    print(f"  Rainy days (>1mm): {(df['precipitation_mm'] > 1).sum()}")
    print(f"  Heavy rain days (>10mm): {(df['precipitation_mm'] > 10).sum()}")
    print(f"  Max daily rainfall: {df['precipitation_mm'].max():.1f} mm")

    # Humidity analysis
    print("\nHUMIDITY (Dewpoint):")
    print(f"  Mean dewpoint: {df['dewpoint_celsius'].mean():.1f}°C")
    print(f"  Range: {df['dewpoint_celsius'].min():.1f}°C to {df['dewpoint_celsius'].max():.1f}°C")
    print(f"  High humidity days (dewpoint >15°C): {(df['dewpoint_celsius'] > 15).sum()}")

    # Identify high-risk periods
    print("\n" + "="*80)
    print("HIGH-RISK PERIOD IDENTIFICATION")
    print("="*80)

    # Define risk thresholds
    # High risk: warm temperature (>25°C), recent rain, high humidity (>12°C dewpoint)
    df['high_temp'] = df['tmean_celsius'] > 25
    df['recent_rain'] = df['precipitation_mm'] > 0.5
    df['high_humidity'] = df['dewpoint_celsius'] > 12
    df['risk_score'] = df['high_temp'].astype(int) + df['recent_rain'].astype(int) + df['high_humidity'].astype(int)

    high_risk_days = df[df['risk_score'] >= 2]

    print(f"\nHigh-risk days (2+ risk factors): {len(high_risk_days)} days ({len(high_risk_days)/len(df)*100:.1f}%)")
    print("\nTop 10 highest-risk days:")
    print(high_risk_days.nlargest(10, 'risk_score')[['date', 'tmean_celsius', 'precipitation_mm', 'dewpoint_celsius', 'risk_score']])

    # Save results
    output_file = "climate_data_health_study_soweto.csv"
    df.to_csv(output_file, index=False)
    print(f"\n\nFull dataset saved to: {output_file}")

    # Create analysis summary
    summary_file = "climate_summary_health_study.csv"
    summary_data = {
        'Metric': [
            'Study Period',
            'Location',
            'Days Analyzed',
            'Mean Max Temperature (°C)',
            'Total Rainfall (mm)',
            'Rainy Days',
            'Mean Dewpoint (°C)',
            'High-Risk Days',
            'High-Risk Percentage'
        ],
        'Value': [
            f"{start_date} to {end_date}",
            location_name,
            len(df),
            f"{df['tmax_celsius'].mean():.1f}",
            f"{df['precipitation_mm'].sum():.1f}",
            (df['precipitation_mm'] > 1).sum(),
            f"{df['dewpoint_celsius'].mean():.1f}",
            len(high_risk_days),
            f"{len(high_risk_days)/len(df)*100:.1f}%"
        ]
    }
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(summary_file, index=False)
    print(f"Summary statistics saved to: {summary_file}")

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\nNext steps for health research:")
    print("1. Merge this climate data with disease surveillance data by date")
    print("2. Analyze correlation between high-risk periods and disease cases")
    print("3. Consider lag effects (disease cases may occur 7-14 days after climate events)")
    print("4. Use regression models to quantify climate-disease relationships")
    print("5. Develop early warning system based on climate thresholds")

if __name__ == "__main__":
    extract_climate_data_for_health_study()
