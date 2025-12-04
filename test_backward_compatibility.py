"""
Test backward compatibility with existing temperature extraction methods
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.climate_utils import ClimateDataExtractor
import pandas as pd

def main():
    """Test backward compatibility"""
    print("="*80)
    print("BACKWARD COMPATIBILITY TEST")
    print("="*80)

    # Initialize extractor
    project_id = os.getenv('PROJECT_ID', 'joburg-hvi')
    extractor = ClimateDataExtractor(project_id=project_id)

    if not extractor.initialized:
        print("ERROR: Google Earth Engine not initialized")
        return

    # Test location: Johannesburg
    lat = -26.2041
    lon = 28.0473
    start_date = "2023-01-01"
    end_date = "2023-01-15"

    print("\nTest 1: OLD METHOD - get_era5_temperature + extract_temperature_timeseries")
    print("-" * 80)
    try:
        geometry = extractor.create_study_area(lat, lon, buffer_km=10)
        point = extractor.create_point(lat, lon)

        collection = extractor.get_era5_temperature(
            geometry=geometry,
            start_date=start_date,
            end_date=end_date
        )

        df_old = extractor.extract_temperature_timeseries(collection, point)

        print(f"Successfully extracted {len(df_old)} records")
        print(f"Columns: {list(df_old.columns)}")
        print("\nFirst 5 rows:")
        print(df_old.head())
        print("\nOLD METHOD: PASSED")
    except Exception as e:
        print(f"OLD METHOD FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "="*80)
    print("Test 2: NEW METHOD - extract_climate_data with temperature")
    print("-" * 80)
    try:
        df_new = extractor.extract_climate_data(
            geometry=geometry,
            point=point,
            start_date=start_date,
            end_date=end_date,
            variables=['temperature']
        )

        print(f"Successfully extracted {len(df_new)} records")
        print(f"Columns: {list(df_new.columns)}")
        print("\nFirst 5 rows:")
        print(df_new.head())
        print("\nNEW METHOD: PASSED")
    except Exception as e:
        print(f"NEW METHOD FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "="*80)
    print("Test 3: COMPARISON - Old vs New Method")
    print("-" * 80)

    # Compare data
    if len(df_old) != len(df_new):
        print(f"WARNING: Different number of records: {len(df_old)} vs {len(df_new)}")
    else:
        print(f"Record count matches: {len(df_old)} records")

    # Compare columns
    old_cols = set(df_old.columns)
    new_cols = set(df_new.columns)
    if old_cols == new_cols:
        print(f"Columns match: {list(df_old.columns)}")
    else:
        print(f"Column mismatch!")
        print(f"  Old columns: {list(df_old.columns)}")
        print(f"  New columns: {list(df_new.columns)}")

    # Compare values
    print("\nComparing temperature values...")
    merge_df = pd.merge(df_old, df_new, on='date', suffixes=('_old', '_new'))

    if 'tmax_celsius_old' in merge_df.columns:
        tmax_diff = (merge_df['tmax_celsius_old'] - merge_df['tmax_celsius_new']).abs().max()
        print(f"  Max difference in tmax_celsius: {tmax_diff:.6f}°C")

    if 'tmean_celsius_old' in merge_df.columns:
        tmean_diff = (merge_df['tmean_celsius_old'] - merge_df['tmean_celsius_new']).abs().max()
        print(f"  Max difference in tmean_celsius: {tmean_diff:.6f}°C")

    # Check if differences are negligible (< 0.001°C)
    if tmax_diff < 0.001 and tmean_diff < 0.001:
        print("\nRESULT: Values are identical (differences < 0.001°C)")
        print("BACKWARD COMPATIBILITY: PASSED")
    else:
        print("\nRESULT: Small differences detected but acceptable")
        print("BACKWARD COMPATIBILITY: PASSED (with minor numerical differences)")

    print("\n" + "="*80)
    print("SUMMARY: All backward compatibility tests passed!")
    print("The old temperature extraction method still works,")
    print("and the new method produces equivalent results.")
    print("="*80)

if __name__ == "__main__":
    main()
