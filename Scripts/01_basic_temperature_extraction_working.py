#!/usr/bin/env python3
"""
Basic Temperature Data Extraction with GEEMAP - Working Version
Fixed version of the notebook that students can run without debugging
"""

import ee
import geemap
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import os

# ============================================================================
# Step 1: Initialize Google Earth Engine
# ============================================================================
print("🚀 Initializing Google Earth Engine...")

# IMPORTANT: Replace with your actual Google Cloud project ID
PROJECT_ID = 'joburg-hvi'  # Update this with your project ID

try:
    ee.Initialize(project=PROJECT_ID)
    print(f"✅ Google Earth Engine initialized successfully with project: {PROJECT_ID}")
except Exception as e:
    print(f"❌ Error: {e}")
    print("Please run 'earthengine authenticate' in your terminal first")
    print("Also ensure your project ID is correct")
    exit(1)

# ============================================================================
# Step 2: Define Study Area
# ============================================================================
print("\n📍 Setting up study area...")

# Define your study location (example: Soweto, South Africa)
study_lat = -26.2678
study_lon = 27.8607
location_name = "Soweto"

# Create a point geometry
study_point = ee.Geometry.Point([study_lon, study_lat])

# Create a buffer area around the point (10km radius)
buffer_km = 10
study_area = study_point.buffer(buffer_km * 1000)  # Convert km to meters

print(f"📍 Study Location: {location_name}")
print(f"📐 Coordinates: {study_lat}, {study_lon}")
print(f"🔄 Buffer radius: {buffer_km} km")

# ============================================================================
# Step 3: Define Time Period
# ============================================================================
print("\n📅 Setting time period...")

# Define time period for analysis (start small for testing)
start_date = '2020-01-01'
end_date = '2020-03-31'

# Calculate the number of days
start_dt = datetime.strptime(start_date, '%Y-%m-%d')
end_dt = datetime.strptime(end_date, '%Y-%m-%d')
num_days = (end_dt - start_dt).days + 1

print(f"📅 Study Period: {start_date} to {end_date}")
print(f"⏱️  Duration: {num_days} days (~{num_days/365.25:.1f} years)")

# ============================================================================
# Step 4: Load and Process Climate Data
# ============================================================================
print("\n🌡️  Loading ERA5 temperature data...")

# Load ERA5-Land daily aggregated data
era5_collection = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR') \
    .filterDate(start_date, end_date) \
    .filterBounds(study_area)

# FIXED: Convert temperature from Kelvin to Celsius using correct band names
def kelvin_to_celsius(image):
    """Convert temperature bands from Kelvin to Celsius using CORRECT band names"""
    # CORRECT ERA5 band names: 'temperature_2m' (mean) and 'temperature_2m_max' (max)
    t_mean = image.select('temperature_2m').subtract(273.15).rename('temperature_2m_celsius')
    t_max = image.select('temperature_2m_max').subtract(273.15).rename('temperature_2m_max_celsius')
    
    return image.addBands([t_mean, t_max]) \
        .copyProperties(image, ['system:time_start'])

# Apply temperature conversion
temperature_data = era5_collection.map(kelvin_to_celsius)

print("✅ Temperature data loaded and converted to Celsius")

# ============================================================================
# Step 5: Extract Temperature Time Series
# ============================================================================
print("\n📊 Extracting temperature time series...")

def extract_daily_temperature(collection, point, start_date, end_date):
    """
    Extract daily temperature time series from ERA5 data
    FIXED version with correct band names and proper error handling
    """
    try:
        # Use the correct band names in the reducer
        reducer = ee.Reducer.mean()
        
        # Get the time series data
        time_series = collection.select(['temperature_2m_celsius', 'temperature_2m_max_celsius']) \
            .getRegion(point, 1000)
        
        # Convert to list and process
        data_list = time_series.getInfo()
        
        # Process the data
        dates = []
        tmean_values = []
        tmax_values = []
        
        # Skip header row
        for row in data_list[1:]:
            if row[4] is not None and row[5] is not None:  # Check for valid data
                # Extract date from timestamp
                date_ms = row[3]
                date_obj = datetime.fromtimestamp(date_ms / 1000)
                
                dates.append(date_obj.date())
                tmax_values.append(row[5])  # temperature_2m_max_celsius
                tmean_values.append(row[4])  # temperature_2m_celsius
        
        # Create DataFrame
        df = pd.DataFrame({
            'date': dates,
            'tmax_celsius': tmax_values,
            'tmean_celsius': tmean_values
        })
        
        # Remove any duplicates and sort
        df = df.drop_duplicates(subset=['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        print(f"✅ Extracted {len(df)} daily temperature records")
        return df
        
    except Exception as e:
        print(f"❌ Error extracting data: {e}")
        return pd.DataFrame()

# Extract the temperature data
daily_temps = extract_daily_temperature(temperature_data, study_point, start_date, end_date)

if not daily_temps.empty:
    print(f"\n📋 First 5 records:")
    print(daily_temps.head())
else:
    print("❌ No data extracted. Check your date range and location.")
    exit(1)

# ============================================================================
# Step 6: Basic Analysis and Visualization
# ============================================================================
print("\n📊 Creating visualizations...")

# Convert date column to datetime
daily_temps['date'] = pd.to_datetime(daily_temps['date'])

# Calculate basic statistics
print("📊 TEMPERATURE STATISTICS:")
print(f"📈 Max Temperature: {daily_temps['tmax_celsius'].max():.1f}°C")
print(f"📉 Min Temperature: {daily_temps['tmean_celsius'].min():.1f}°C")
print(f"📊 Mean Temperature: {daily_temps['tmean_celsius'].mean():.1f}°C")

# Create plots
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# Time series plot
axes[0].plot(daily_temps['date'], daily_temps['tmax_celsius'], 
            'r-', alpha=0.7, linewidth=0.8, label='Daily Maximum')
axes[0].plot(daily_temps['date'], daily_temps['tmean_celsius'], 
            'b-', alpha=0.7, linewidth=0.8, label='Daily Mean')
axes[0].set_title(f'Daily Temperature Time Series - {location_name}')
axes[0].set_ylabel('Temperature (°C)')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Temperature distribution
axes[1].hist(daily_temps['tmax_celsius'], bins=20, alpha=0.7, 
            color='red', label='Max Temperature', density=True)
axes[1].hist(daily_temps['tmean_celsius'], bins=20, alpha=0.7, 
            color='blue', label='Mean Temperature', density=True)
axes[1].set_title('Temperature Distribution')
axes[1].set_xlabel('Temperature (°C)')
axes[1].set_ylabel('Density')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# ============================================================================
# Step 7: Calculate Monthly Averages
# ============================================================================
print("\n📊 Calculating monthly averages...")

# Add year and month columns
daily_temps['year'] = daily_temps['date'].dt.year
daily_temps['month'] = daily_temps['date'].dt.month
daily_temps['year_month'] = daily_temps['date'].dt.to_period('M')

# Calculate monthly averages
monthly_averages = daily_temps.groupby('year_month').agg({
    'tmax_celsius': 'mean',
    'tmean_celsius': 'mean'
}).reset_index()

# Add date column for plotting
monthly_averages['date'] = monthly_averages['year_month'].dt.to_timestamp()

print(f"✅ Calculated averages for {len(monthly_averages)} months")

# Plot monthly averages
plt.figure(figsize=(12, 6))
plt.plot(monthly_averages['date'], monthly_averages['tmax_celsius'], 
         'ro-', label='Monthly Avg Maximum Temp', markersize=4)
plt.plot(monthly_averages['date'], monthly_averages['tmean_celsius'], 
         'bo-', label='Monthly Avg Mean Temp', markersize=4)
plt.title(f'Monthly Temperature Averages - {location_name}')
plt.xlabel('Date')
plt.ylabel('Temperature (°C)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# ============================================================================
# Step 8: Export Data
# ============================================================================
print("\n💾 Exporting data...")

# Create export directory
os.makedirs('../data', exist_ok=True)

# Prepare data for export
daily_export = daily_temps[['date', 'tmax_celsius', 'tmean_celsius']].copy()
monthly_export = monthly_averages[['year_month', 'tmax_celsius', 'tmean_celsius']].copy()
monthly_export.columns = ['month', 'avg_tmax_celsius', 'avg_tmean_celsius']

# Export to CSV
daily_filename = f"../data/{location_name.lower().replace(' ', '_')}_daily_temp_{start_date[:4]}_{end_date[:4]}.csv"
monthly_filename = f"../data/{location_name.lower().replace(' ', '_')}_monthly_temp_{start_date[:4]}_{end_date[:4]}.csv"

daily_export.to_csv(daily_filename, index=False)
monthly_export.to_csv(monthly_filename, index=False)

# Export to Excel
excel_filename = f"../data/{location_name.lower().replace(' ', '_')}_temperature_data_{start_date[:4]}_{end_date[:4]}.xlsx"
with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
    daily_export.to_excel(writer, sheet_name='Daily_Data', index=False)
    monthly_export.to_excel(writer, sheet_name='Monthly_Averages', index=False)

print("💾 Data exported successfully!")
print(f"📁 Files created:")
print(f"   • {daily_filename}")
print(f"   • {monthly_filename}")
print(f"   • {excel_filename}")

print(f"\n📊 Summary:")
print(f"   • Daily records: {len(daily_export)}")
print(f"   • Monthly records: {len(monthly_export)}")
print(f"   • Temperature range: {daily_temps['tmean_celsius'].min():.1f}°C to {daily_temps['tmean_celsius'].max():.1f}°C")

print(f"\n🎉 COMPLETED SUCCESSFULLY!")
print(f"Your temperature data for {location_name} has been extracted and exported.")
print(f"You can now use this data for your health research analysis!")
