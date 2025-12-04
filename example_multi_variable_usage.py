"""
Example: How to use the new multi-variable climate data extraction

This script demonstrates the new extract_climate_data() method that supports
extraction of multiple climate variables in a single call.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.climate_utils import ClimateDataExtractor

def example_single_variable():
    """Example: Extract a single variable"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Extract Single Variable (Precipitation)")
    print("="*80)

    extractor = ClimateDataExtractor(project_id='joburg-hvi')

    # Define location and date range
    lat, lon = -26.2041, 28.0473  # Johannesburg
    start_date = "2023-01-01"
    end_date = "2023-01-31"

    # Create geometry
    geometry = extractor.create_study_area(lat, lon, buffer_km=10)
    point = extractor.create_point(lat, lon)

    # Extract precipitation data
    df = extractor.extract_climate_data(
        geometry=geometry,
        point=point,
        start_date=start_date,
        end_date=end_date,
        variables=['precipitation']  # Single variable
    )

    print(f"\nExtracted {len(df)} records")
    print(f"Columns: {list(df.columns)}")
    print("\nSample data:")
    print(df.head())

def example_multiple_variables():
    """Example: Extract multiple variables together"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Extract Multiple Variables (Temp + Precip + Wind)")
    print("="*80)

    extractor = ClimateDataExtractor(project_id='joburg-hvi')

    lat, lon = -26.2041, 28.0473
    start_date = "2023-06-01"
    end_date = "2023-06-30"

    geometry = extractor.create_study_area(lat, lon, buffer_km=10)
    point = extractor.create_point(lat, lon)

    # Extract multiple variables
    df = extractor.extract_climate_data(
        geometry=geometry,
        point=point,
        start_date=start_date,
        end_date=end_date,
        variables=['temperature', 'precipitation', 'wind']  # Multiple variables
    )

    print(f"\nExtracted {len(df)} records with {len(df.columns)-1} variables")
    print(f"Columns: {list(df.columns)}")
    print("\nSample data:")
    print(df.head())

def example_all_variables():
    """Example: Extract all available variables"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Extract All Variables")
    print("="*80)

    extractor = ClimateDataExtractor(project_id='joburg-hvi')

    lat, lon = -33.9249, 18.4241  # Cape Town
    start_date = "2023-12-01"
    end_date = "2023-12-31"

    geometry = extractor.create_study_area(lat, lon, buffer_km=10)
    point = extractor.create_point(lat, lon)

    # Extract all variables
    df = extractor.extract_climate_data(
        geometry=geometry,
        point=point,
        start_date=start_date,
        end_date=end_date,
        variables=[
            'temperature',
            'precipitation',
            'humidity',
            'wind',
            'solar',
            'pressure',
            'evapotranspiration'
        ]
    )

    print(f"\nExtracted {len(df)} records with {len(df.columns)-1} variables")
    print(f"Columns: {list(df.columns)}")
    print("\nSample data:")
    print(df.head())

    # Save to CSV
    output_file = "example_all_variables_cape_town.csv"
    df.to_csv(output_file, index=False)
    print(f"\nData saved to: {output_file}")

def example_variable_descriptions():
    """Display information about available variables"""
    print("\n" + "="*80)
    print("AVAILABLE CLIMATE VARIABLES")
    print("="*80)

    variables = {
        'temperature': {
            'description': 'Air temperature',
            'columns': ['tmax_celsius', 'tmean_celsius'],
            'units': '°C',
            'source': 'temperature_2m_max, temperature_2m',
            'conversion': 'Kelvin to Celsius (subtract 273.15)'
        },
        'precipitation': {
            'description': 'Total precipitation',
            'columns': ['precipitation_mm'],
            'units': 'mm',
            'source': 'total_precipitation_sum',
            'conversion': 'meters to millimeters (multiply by 1000)'
        },
        'humidity': {
            'description': 'Humidity (dewpoint temperature)',
            'columns': ['dewpoint_celsius'],
            'units': '°C',
            'source': 'dewpoint_temperature_2m',
            'conversion': 'Kelvin to Celsius (subtract 273.15)'
        },
        'wind': {
            'description': 'Wind speed and components',
            'columns': ['wind_speed_ms', 'wind_u_ms', 'wind_v_ms'],
            'units': 'm/s',
            'source': 'u_component_of_wind_10m, v_component_of_wind_10m',
            'conversion': 'Wind speed calculated as sqrt(u² + v²)'
        },
        'solar': {
            'description': 'Solar radiation',
            'columns': ['solar_radiation_jm2'],
            'units': 'J/m²',
            'source': 'surface_solar_radiation_downwards_sum',
            'conversion': 'None (already in J/m²)'
        },
        'pressure': {
            'description': 'Surface pressure',
            'columns': ['surface_pressure_pa'],
            'units': 'Pa',
            'source': 'surface_pressure',
            'conversion': 'None (already in Pa)'
        },
        'evapotranspiration': {
            'description': 'Potential evapotranspiration',
            'columns': ['evapotranspiration_mm'],
            'units': 'mm',
            'source': 'potential_evaporation_sum',
            'conversion': 'meters to millimeters (multiply by 1000), absolute value'
        }
    }

    for var_name, info in variables.items():
        print(f"\n{var_name.upper()}")
        print(f"  Description: {info['description']}")
        print(f"  Columns: {', '.join(info['columns'])}")
        print(f"  Units: {info['units']}")
        print(f"  ERA5 Source: {info['source']}")
        print(f"  Conversion: {info['conversion']}")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("MULTI-VARIABLE CLIMATE DATA EXTRACTION EXAMPLES")
    print("="*80)

    # Show variable information first
    example_variable_descriptions()

    # Run examples (commented out to avoid actual API calls)
    # Uncomment to run:
    # example_single_variable()
    # example_multiple_variables()
    # example_all_variables()

    print("\n" + "="*80)
    print("To run the extraction examples, uncomment the function calls above")
    print("="*80)
