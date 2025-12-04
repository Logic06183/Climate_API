"""
Test script for multi-variable climate data extraction
Tests each variable individually and all variables together
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.climate_utils import ClimateDataExtractor
import pandas as pd

def test_variable_extraction(extractor, variables, test_name):
    """Test extraction of specific variables"""
    print("\n" + "="*80)
    print(f"TEST: {test_name}")
    print("="*80)

    # Test location: Johannesburg
    lat = -26.2041
    lon = 28.0473

    # Short date range for quick testing
    start_date = "2023-01-01"
    end_date = "2023-01-31"

    try:
        # Create geometry
        geometry = extractor.create_study_area(lat, lon, buffer_km=10)
        point = extractor.create_point(lat, lon)

        # Extract data
        print(f"\nExtracting variables: {variables}")
        df = extractor.extract_climate_data(
            geometry=geometry,
            point=point,
            start_date=start_date,
            end_date=end_date,
            variables=variables
        )

        # Display results
        print(f"\nExtracted {len(df)} records")
        print(f"Columns: {list(df.columns)}")
        print("\nFirst 5 rows:")
        print(df.head())
        print("\nData summary:")
        print(df.describe())

        # Save to CSV
        output_file = f"test_output_{test_name.replace(' ', '_').lower()}.csv"
        df.to_csv(output_file, index=False)
        print(f"\nSaved to: {output_file}")

        return True, df

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    """Run all tests"""
    print("="*80)
    print("MULTI-VARIABLE CLIMATE DATA EXTRACTION TESTS")
    print("="*80)

    # Initialize extractor
    project_id = os.getenv('PROJECT_ID', 'joburg-hvi')
    extractor = ClimateDataExtractor(project_id=project_id)

    if not extractor.initialized:
        print("ERROR: Google Earth Engine not initialized")
        return

    results = {}

    # Test 1: Temperature (baseline - backward compatibility)
    success, df = test_variable_extraction(
        extractor,
        ['temperature'],
        "Temperature Only (Backward Compatibility)"
    )
    results['temperature'] = success

    # Test 2: Precipitation
    success, df = test_variable_extraction(
        extractor,
        ['precipitation'],
        "Precipitation"
    )
    results['precipitation'] = success

    # Test 3: Humidity (Dewpoint)
    success, df = test_variable_extraction(
        extractor,
        ['humidity'],
        "Humidity (Dewpoint)"
    )
    results['humidity'] = success

    # Test 4: Wind
    success, df = test_variable_extraction(
        extractor,
        ['wind'],
        "Wind (Speed and Components)"
    )
    results['wind'] = success

    # Test 5: Solar Radiation
    success, df = test_variable_extraction(
        extractor,
        ['solar'],
        "Solar Radiation"
    )
    results['solar'] = success

    # Test 6: Surface Pressure
    success, df = test_variable_extraction(
        extractor,
        ['pressure'],
        "Surface Pressure"
    )
    results['pressure'] = success

    # Test 7: Evapotranspiration
    success, df = test_variable_extraction(
        extractor,
        ['evapotranspiration'],
        "Evapotranspiration"
    )
    results['evapotranspiration'] = success

    # Test 8: Multiple variables together
    success, df = test_variable_extraction(
        extractor,
        ['temperature', 'precipitation', 'humidity', 'wind', 'solar', 'pressure', 'evapotranspiration'],
        "All Variables Combined"
    )
    results['all_variables'] = success

    # Test 9: Custom combination
    success, df = test_variable_extraction(
        extractor,
        ['temperature', 'precipitation', 'wind'],
        "Custom Combination (Temp + Precip + Wind)"
    )
    results['custom_combo'] = success

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test_name, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"{test_name:30s}: {status}")

    total_tests = len(results)
    passed_tests = sum(results.values())
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("\nALL TESTS PASSED!")
    else:
        print(f"\n{total_tests - passed_tests} TESTS FAILED")

if __name__ == "__main__":
    main()
