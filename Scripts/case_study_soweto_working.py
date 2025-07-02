#!/usr/bin/env python3
"""
Soweto Climate-Health Case Study - Working Version
Fixed version based on the successful extraction script
"""

import ee
import geemap
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime, timedelta
import os

# ============================================================================
# Step 1: Initialize Google Earth Engine
# ============================================================================
print("🚀 Initializing Google Earth Engine for Soweto Case Study...")

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
# Step 2: Define Soweto Study Area
# ============================================================================
print("\n📍 Setting up Soweto study area...")

# Soweto coordinates (center of the township)
soweto_lat = -26.2678
soweto_lon = 27.8607
location_name = "Soweto, South Africa"

# Create point and area geometries
soweto_point = ee.Geometry.Point([soweto_lon, soweto_lat])
soweto_area = soweto_point.buffer(10000)  # 10km buffer

print(f"📍 Study Location: {location_name}")
print(f"📐 Coordinates: {soweto_lat}, {soweto_lon}")
print(f"🔄 Buffer radius: 10 km")

# ============================================================================
# Step 3: Define Study Period (Health Research Context)
# ============================================================================
print("\n📅 Setting study period for health analysis...")

# Health research period: April 2016 - March 2022 (6 years)
# This matches typical pregnancy/birth cohort studies
start_date = '2016-04-01'  # Full study period
end_date = '2022-03-31'

# For testing, use a smaller period first
# start_date = '2020-01-01'  # Uncomment for testing
# end_date = '2020-03-31'    # Uncomment for testing

start_dt = datetime.strptime(start_date, '%Y-%m-%d')
end_dt = datetime.strptime(end_date, '%Y-%m-%d')
num_days = (end_dt - start_dt).days + 1

print(f"📅 Study Period: {start_date} to {end_date}")
print(f"⏱️  Duration: {num_days} days (~{num_days/365.25:.1f} years)")
print("🏥 Perfect for climate-health research (preterm births, heat stress)")

# ============================================================================
# Step 4: Extract ERA5 Temperature Data (FIXED VERSION)
# ============================================================================
print(f"\n🌡️  Extracting ERA5 temperature data for {location_name}...")

def get_era5_temperature_data(start_date, end_date, geometry):
    """
    Extract ERA5 temperature data - FIXED VERSION with correct band names
    """
    print(f"Loading ERA5 data from {start_date} to {end_date}...")
    
    # Load ERA5-Land daily data
    collection = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR') \
        .filterDate(start_date, end_date) \
        .filterBounds(geometry)
    
    # FIXED: Temperature conversion with correct band names
    def kelvin_to_celsius(image):
        """Convert temperature from Kelvin to Celsius using CORRECT band names"""
        # CORRECT ERA5 band names: 'temperature_2m' and 'temperature_2m_max'
        t_mean = image.select('temperature_2m').subtract(273.15).rename('temperature_2m_celsius')
        t_max = image.select('temperature_2m_max').subtract(273.15).rename('temperature_2m_max_celsius')
        
        return image.addBands([t_mean, t_max]) \
            .copyProperties(image, ['system:time_start'])
    
    processed_collection = collection.map(kelvin_to_celsius)
    
    print(f"✅ Loaded {processed_collection.size().getInfo()} daily records")
    return processed_collection

# Extract temperature data
temp_collection = get_era5_temperature_data(start_date, end_date, soweto_area)

# ============================================================================
# Step 5: Convert to DataFrame (Chunked Extraction)
# ============================================================================
print("\n📊 Converting to DataFrame using chunked extraction...")

def extract_temperature_timeseries_chunked(collection, point, start_date, end_date, chunk_days=90):
    """
    Extract temperature time series using chunked approach - FIXED VERSION
    """
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    total_days = (end_dt - start_dt).days + 1
    
    all_dates = []
    all_tmax = []
    all_tmean = []
    
    current_date = start_dt
    chunk_num = 0
    
    while current_date < end_dt:
        chunk_num += 1
        chunk_end = min(current_date + timedelta(days=chunk_days), end_dt)
        
        print(f"  Processing chunk {chunk_num}: {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}")
        
        # Filter collection for this chunk
        chunk_collection = collection.filterDate(
            current_date.strftime('%Y-%m-%d'),
            chunk_end.strftime('%Y-%m-%d')
        )
        
        try:
            # Extract data for this chunk
            region_data = chunk_collection.select(['temperature_2m_celsius', 'temperature_2m_max_celsius']) \
                .getRegion(point, 1000)
            
            data_list = region_data.getInfo()
            
            # Process chunk data (skip header)
            for row in data_list[1:]:
                if row[4] is not None and row[5] is not None:
                    # Extract date from timestamp
                    date_ms = row[3]
                    date_obj = datetime.fromtimestamp(date_ms / 1000)
                    
                    all_dates.append(date_obj.date())
                    all_tmean.append(row[4])  # temperature_2m_celsius
                    all_tmax.append(row[5])   # temperature_2m_max_celsius
            
            print(f"    ✅ Chunk {chunk_num} completed ({len(data_list)-1} records)")
            
        except Exception as e:
            print(f"    ❌ Error in chunk {chunk_num}: {e}")
        
        current_date = chunk_end
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': all_dates,
        'tmax_celsius': all_tmax,
        'tmean_celsius': all_tmean
    })
    
    # Clean data
    df = df.drop_duplicates(subset=['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    print(f"✅ Successfully extracted {len(df)} daily temperature records")
    return df

# Extract the time series
temp_df = extract_temperature_timeseries_chunked(temp_collection, soweto_point, start_date, end_date)

if temp_df.empty:
    print("❌ No data extracted. Check your date range and authentication.")
    exit(1)

print(f"\n📋 First 5 records:")
print(temp_df.head())

print(f"\n📊 Temperature Summary:")
print(f"📈 Max Temperature: {temp_df['tmax_celsius'].max():.1f}°C")
print(f"📉 Min Temperature: {temp_df['tmean_celsius'].min():.1f}°C") 
print(f"📊 Mean Temperature: {temp_df['tmean_celsius'].mean():.1f}°C")

# ============================================================================
# Step 6: Monthly Aggregation for Health Analysis
# ============================================================================
print(f"\n📊 Calculating monthly averages for health analysis...")

# Convert date to datetime and add temporal columns
temp_df['date'] = pd.to_datetime(temp_df['date'])
temp_df['year'] = temp_df['date'].dt.year
temp_df['month'] = temp_df['date'].dt.month
temp_df['year_month'] = temp_df['date'].dt.to_period('M')

# Calculate monthly statistics
monthly_stats = temp_df.groupby('year_month').agg({
    'tmax_celsius': ['mean', 'max', 'std'],
    'tmean_celsius': ['mean', 'max', 'std']
}).round(2)

# Flatten column names
monthly_stats.columns = ['_'.join(col).strip() for col in monthly_stats.columns]
monthly_stats = monthly_stats.reset_index()

# Add date column for plotting
monthly_stats['date'] = monthly_stats['year_month'].dt.to_timestamp()

print(f"✅ Calculated statistics for {len(monthly_stats)} months")
print(f"\n📋 Monthly Statistics (first 5 months):")
print(monthly_stats[['year_month', 'tmax_celsius_mean', 'tmean_celsius_mean']].head())

# ============================================================================
# Step 7: Health-Focused Visualizations
# ============================================================================
print(f"\n📊 Creating health-focused visualizations...")

# Set up the plotting style
plt.style.use('default')
sns.set_palette("husl")

# Create comprehensive visualization
fig = plt.figure(figsize=(16, 12))

# 1. Time series of monthly averages
ax1 = plt.subplot(3, 2, 1)
plt.plot(monthly_stats['date'], monthly_stats['tmax_celsius_mean'], 
         'ro-', label='Max Temperature', markersize=3, linewidth=1)
plt.plot(monthly_stats['date'], monthly_stats['tmean_celsius_mean'], 
         'bo-', label='Mean Temperature', markersize=3, linewidth=1)
plt.title(f'Monthly Temperature Trends - {location_name}')
plt.ylabel('Temperature (°C)')
plt.legend()
plt.grid(True, alpha=0.3)

# 2. Seasonal patterns (box plot by month)
ax2 = plt.subplot(3, 2, 2)
temp_df['month_name'] = temp_df['date'].dt.month_name()
month_order = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']
sns.boxplot(data=temp_df, x='month', y='tmean_celsius', ax=ax2)
plt.title('Seasonal Temperature Patterns')
plt.xlabel('Month')
plt.ylabel('Mean Temperature (°C)')
plt.xticks(range(12), [m[:3] for m in month_order])

# 3. Temperature distribution
ax3 = plt.subplot(3, 2, 3)
plt.hist(temp_df['tmean_celsius'], bins=30, alpha=0.7, color='blue', density=True)
plt.axvline(temp_df['tmean_celsius'].mean(), color='red', linestyle='--', 
           label=f'Mean: {temp_df["tmean_celsius"].mean():.1f}°C')
plt.title('Temperature Distribution')
plt.xlabel('Temperature (°C)')
plt.ylabel('Density')
plt.legend()

# 4. Heat stress analysis (days above thresholds)
ax4 = plt.subplot(3, 2, 4)
# Define heat stress thresholds for health analysis
heat_thresholds = [25, 30, 35]  # °C
heat_days = []

for threshold in heat_thresholds:
    days_above = temp_df[temp_df['tmax_celsius'] > threshold].groupby('year').size()
    heat_days.append(days_above)

# Plot heat stress days by year
years = temp_df['year'].unique()
x = np.arange(len(years))
width = 0.25

for i, threshold in enumerate(heat_thresholds):
    if len(heat_days[i]) > 0:
        plt.bar(x + i*width, [heat_days[i].get(year, 0) for year in years], 
               width, label=f'>{threshold}°C')

plt.title('Heat Stress Days by Year')
plt.xlabel('Year')
plt.ylabel('Days Above Threshold')
plt.legend()
plt.xticks(x + width, years)

# 5. Yearly temperature trends
ax5 = plt.subplot(3, 2, 5)
yearly_temps = temp_df.groupby('year')['tmean_celsius'].mean()
plt.plot(yearly_temps.index, yearly_temps.values, 'go-', markersize=6)
plt.title('Annual Mean Temperature Trend')
plt.xlabel('Year')
plt.ylabel('Mean Temperature (°C)')
plt.grid(True, alpha=0.3)

# 6. Temperature variability (monthly standard deviation)
ax6 = plt.subplot(3, 2, 6)
plt.plot(monthly_stats['date'], monthly_stats['tmean_celsius_std'], 
         'mo-', markersize=3, linewidth=1)
plt.title('Monthly Temperature Variability')
plt.xlabel('Date')
plt.ylabel('Temperature Std Dev (°C)')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# ============================================================================
# Step 8: Export Data for Health Research
# ============================================================================
print(f"\n💾 Exporting data for health research...")

# Create export directory
os.makedirs('../data', exist_ok=True)

# Prepare datasets for health analysis
daily_export = temp_df[['date', 'tmax_celsius', 'tmean_celsius', 'year', 'month']].copy()
monthly_export = monthly_stats[['year_month', 'tmax_celsius_mean', 'tmean_celsius_mean',
                               'tmax_celsius_max', 'tmax_celsius_std', 'tmean_celsius_std']].copy()

# Create heat stress indicators
daily_export['heat_stress_mild'] = (daily_export['tmax_celsius'] > 25).astype(int)
daily_export['heat_stress_moderate'] = (daily_export['tmax_celsius'] > 30).astype(int)  
daily_export['heat_stress_severe'] = (daily_export['tmax_celsius'] > 35).astype(int)

# Monthly heat stress days
heat_stress_monthly = daily_export.groupby(['year', 'month']).agg({
    'heat_stress_mild': 'sum',
    'heat_stress_moderate': 'sum', 
    'heat_stress_severe': 'sum'
}).reset_index()

# Export files
base_name = f"soweto_climate_health_data_{start_date[:4]}_{end_date[:4]}"

# CSV exports
daily_filename = f"../data/{base_name}_daily.csv"
monthly_filename = f"../data/{base_name}_monthly.csv"
heat_stress_filename = f"../data/{base_name}_heat_stress.csv"

daily_export.to_csv(daily_filename, index=False)
monthly_export.to_csv(monthly_filename, index=False)
heat_stress_monthly.to_csv(heat_stress_filename, index=False)

# Excel export with multiple sheets
excel_filename = f"../data/{base_name}_complete.xlsx"
with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
    daily_export.to_excel(writer, sheet_name='Daily_Temperature', index=False)
    monthly_export.to_excel(writer, sheet_name='Monthly_Statistics', index=False)
    heat_stress_monthly.to_excel(writer, sheet_name='Heat_Stress_Days', index=False)

print("💾 Data exported successfully!")
print(f"📁 Files created:")
print(f"   • {daily_filename}")
print(f"   • {monthly_filename}")
print(f"   • {heat_stress_filename}")
print(f"   • {excel_filename}")

# ============================================================================
# Summary for Health Researchers
# ============================================================================
print(f"\n🏥 SOWETO CLIMATE-HEALTH DATA SUMMARY")
print(f"=" * 50)
print(f"📍 Location: {location_name}")
print(f"📅 Study Period: {start_date} to {end_date}")
print(f"📊 Daily records: {len(daily_export)}")
print(f"📊 Monthly records: {len(monthly_export)}")
print(f"🌡️  Temperature range: {temp_df['tmean_celsius'].min():.1f}°C to {temp_df['tmax_celsius'].max():.1f}°C")

# Heat stress summary
total_mild_days = daily_export['heat_stress_mild'].sum()
total_moderate_days = daily_export['heat_stress_moderate'].sum()
total_severe_days = daily_export['heat_stress_severe'].sum()

print(f"\n🔥 HEAT STRESS ANALYSIS:")
print(f"   • Mild heat stress days (>25°C): {total_mild_days}")
print(f"   • Moderate heat stress days (>30°C): {total_moderate_days}")
print(f"   • Severe heat stress days (>35°C): {total_severe_days}")

print(f"\n📈 RESEARCH APPLICATIONS:")
print(f"   • Correlate monthly temperatures with preterm birth rates")
print(f"   • Analyze heat stress days vs. health outcomes")
print(f"   • Study seasonal patterns in temperature and health")
print(f"   • Investigate temperature variability effects")

print(f"\n🎉 CASE STUDY COMPLETED SUCCESSFULLY!")
print(f"Your Soweto climate data is ready for health research analysis!")
