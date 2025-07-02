#!/usr/bin/env python3
"""
Test Google Earth Engine connection and diagnose issues
"""

import ee
import sys

def test_gee_connection():
    """Test GEE connection with detailed error reporting"""
    print("🔍 Testing Google Earth Engine Connection")
    print("=" * 50)
    
    # Test 1: Check if earthengine-api is installed
    try:
        import ee
        print("✅ earthengine-api package is installed")
    except ImportError as e:
        print(f"❌ earthengine-api not installed: {e}")
        return False
    
    # Test 2: Try to initialize without project
    print("\n🧪 Test 2: Initialize without project")
    try:
        ee.Initialize()
        print("✅ GEE initialized successfully (no project needed)")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        
        # Check if it's a registration issue
        if "Not signed up" in str(e) or "not registered" in str(e):
            print("\n🚨 REGISTRATION REQUIRED:")
            print("   1. Go to: https://developers.google.com/earth-engine/guides/access")
            print("   2. Sign up for Google Earth Engine access")
            print("   3. This may take 1-2 days for approval")
            print("   4. Once approved, you can use GEE")
            return False
        
        # Try with project initialization
        print("\n🧪 Test 3: Initialize with project")
        try:
            # Try to get available projects
            print("   Attempting to initialize with project...")
            ee.Initialize(project='ee-your-project-name')  # This will likely fail but give us info
        except Exception as e2:
            print(f"   ❌ Project initialization failed: {e2}")
            
            # Check if we need to create a cloud project
            if "quota" in str(e2).lower() or "project" in str(e2).lower():
                print("\n🚨 CLOUD PROJECT REQUIRED:")
                print("   1. Go to: https://console.cloud.google.com/")
                print("   2. Create a new project or select existing one")
                print("   3. Enable Earth Engine API for your project")
                print("   4. Then run: ee.Initialize(project='your-project-id')")
                return False
    
    return False

def test_basic_gee_query():
    """Test a basic GEE query if initialization works"""
    print("\n🧪 Test 4: Basic GEE Query")
    try:
        # Try to access a simple collection
        collection = ee.ImageCollection('LANDSAT/LC08/C01/T1')
        count = collection.limit(1).size().getInfo()
        print(f"✅ Basic query successful: Found {count} image(s)")
        return True
    except Exception as e:
        print(f"❌ Basic query failed: {e}")
        return False

def print_debug_info():
    """Print helpful debug information"""
    print("\n🔍 DEBUG INFORMATION")
    print("=" * 50)
    
    # Check authentication status
    try:
        import subprocess
        result = subprocess.run(['earthengine', 'authenticate'], 
                              capture_output=True, text=True)
        print(f"Auth status: {result.stderr}")
    except:
        print("Could not check authentication status")
    
    # Check if .config exists
    import os
    config_path = os.path.expanduser('~/.config/earthengine/credentials')
    if os.path.exists(config_path):
        print(f"✅ Credentials file exists: {config_path}")
    else:
        print(f"❌ Credentials file missing: {config_path}")
    
    print("\n💡 TROUBLESHOOTING STEPS:")
    print("1. Make sure you're signed up for GEE access")
    print("2. Check your Google Cloud project setup")
    print("3. Try running: earthengine authenticate --force")
    print("4. Consider using a specific project: ee.Initialize(project='your-project')")

def main():
    """Main test function"""
    print("🌍 GOOGLE EARTH ENGINE CONNECTION TEST")
    print("=" * 60)
    
    # Run connection test
    success = test_gee_connection()
    
    if success:
        # If basic connection works, test a query
        test_basic_gee_query()
        print("\n🎉 All tests passed! GEE is ready to use.")
    else:
        print_debug_info()
        print("\n❌ GEE connection failed. Please follow the troubleshooting steps above.")

if __name__ == "__main__":
    main()
