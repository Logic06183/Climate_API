#!/usr/bin/env python3
"""
Test script for multi-variable climate data extraction
"""

import requests
import json
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:8000"

def test_extraction(test_name, variables, location_name="Test Soweto"):
    """Test extraction with specified variables"""
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"Variables: {variables}")
    print(f"{'='*60}")

    # Calculate date range (last 7 days for quick testing)
    end_date = datetime(2024, 1, 7)
    start_date = datetime(2024, 1, 1)

    payload = {
        "location_name": location_name,
        "latitude": -26.2678,
        "longitude": 27.8607,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "buffer_km": 10,
        "variables": variables
    }

    try:
        response = requests.post(f"{API_BASE_URL}/extract", json=payload, timeout=120)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data['status']}")
            print(f"📊 Records extracted: {data['records_extracted']}")
            print(f"📝 Message: {data['message']}")

            # Show available statistics
            if data.get('temperature_range'):
                print(f"\n📈 Available statistics:")
                for stat_type, stats in data['temperature_range'].items():
                    print(f"  - {stat_type}: {stats}")

            # Show data columns
            if data.get('data') and data['data'].get('daily'):
                first_record = data['data']['daily'][0]
                print(f"\n🔍 Data columns: {list(first_record.keys())}")
                print(f"\n📅 Sample record (first day):")
                for key, value in first_record.items():
                    if isinstance(value, float):
                        print(f"  - {key}: {value:.2f}")
                    else:
                        print(f"  - {key}: {value}")

            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def main():
    print("🌍 Testing Multi-Variable Climate Data Extraction API")
    print("=" * 60)

    tests = [
        ("Temperature Only", ["temperature"]),
        ("Temperature + Precipitation", ["temperature", "precipitation"]),
        ("Temperature + Wind", ["temperature", "wind"]),
        ("All Variables", ["temperature", "precipitation", "humidity", "wind", "solar", "pressure", "evapotranspiration"]),
    ]

    results = []
    for test_name, variables in tests:
        success = test_extraction(test_name, variables)
        results.append((test_name, success))

    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Multi-variable extraction is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")

if __name__ == "__main__":
    main()
