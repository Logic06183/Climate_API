#!/usr/bin/env python3
"""
Climate Data Extraction Script for Health Research

This script demonstrates how to extract climate data from Google Earth Engine
in manageable chunks for health research applications.

Example: Extract temperature data for Soweto, South Africa (April 2016 - March 2022)
Usage: python extract_climate_data.py
"""

import ee
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import argparse
import sys

def initialize_earth_engine(project_id='joburg-hvi'):
    """Initialize Google Earth Engine with project"""
    try:
        ee.Initialize(project=project_id)
        print(f"✅ Google Earth Engine initialized successfully with project: {project_id}")
        return True
    except Exception as e:
        print(f"❌ Error initializing Google Earth Engine: {e}")
        if "not registered" in str(e) or "Not signed up" in str(e):
            print("Please ensure your project is registered for Earth Engine access")
        print("Available troubleshooting:")
        print("  1. Run: earthengine authenticate --force")
        print("  2. Ensure your Google Cloud project has Earth Engine enabled")
        print("  3. Try a different project ID")
        return False

def create_study_area(lat, lon, buffer_km=10):
    """Create study area geometry from coordinates"""
    point = ee.Geometry.Point([lon, lat])
    area = point.buffer(buffer_km * 1000)  # Convert km to meters
    return point, area

def get_era5_temperature_data(geometry, start_date, end_date):
    """Load ERA5 temperature data and convert to Celsius"""
    print(f"📊 Loading ERA5 data from {start_date} to {end_date}...")
    
    collection = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR') \
        .filterDate(start_date, end_date) \
        .filterBounds(geometry)
    
    # Convert temperature from Kelvin to Celsius and select bands
    def kelvin_to_celsius(image):
        # Convert temperature bands from Kelvin to Celsius
        t_mean = image.select('temperature_2m').subtract(273.15).rename('temperature_2m_celsius')
        t_max = image.select('temperature_2m_max').subtract(273.15).rename('temperature_2m_max_celsius')
        
        return image.addBands([t_mean, t_max]).select(['temperature_2m_celsius', 'temperature_2m_max_celsius']).copyProperties(image, ['system:time_start'])
    
    temp_data = collection.map(kelvin_to_celsius)
    
    data_count = temp_data.size().getInfo()
    print(f"✅ Found {data_count} daily temperature records")
    
    return temp_data

def extract_temperature_timeseries_chunked(collection, point, start_date, end_date, chunk_days=90):
    """
    Extract temperature time series in chunks to manage memory and API limits
    """
    print(f"🔄 Extracting temperature time series in {chunk_days}-day chunks...")
    
    # Create date range
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    all_data = []
    current_date = start_dt
    chunk_num = 1
    
    while current_date < end_dt:
        # Calculate chunk end date
        chunk_end = min(current_date + timedelta(days=chunk_days), end_dt)
        
        chunk_start_str = current_date.strftime('%Y-%m-%d')
        chunk_end_str = chunk_end.strftime('%Y-%m-%d')
        
        print(f"  Processing chunk {chunk_num}: {chunk_start_str} to {chunk_end_str}")
        
        try:
            # Filter collection for this chunk
            chunk_collection = collection.filterDate(chunk_start_str, chunk_end_str)
            
            # Extract data for this chunk
            chunk_data = chunk_collection.getRegion(point, 1000).getInfo()
            
            if len(chunk_data) > 1:  # Check if we have data (header + data rows)
                # Process chunk data
                header = chunk_data[0]
                data_rows = chunk_data[1:]
                
                for row in data_rows:
                    if row[4] is not None and row[5] is not None:  # Check for valid data
                        date_ms = row[3]
                        date_obj = datetime.fromtimestamp(date_ms / 1000)
                        
                        all_data.append({
                            'date': date_obj.date(),
                            'tmax_celsius': row[4],
                            'tmean_celsius': row[5]
                        })
            
            print(f"    ✅ Chunk {chunk_num} completed ({len(chunk_data)-1 if len(chunk_data) > 1 else 0} records)")
            
        except Exception as e:
            print(f"    ❌ Error processing chunk {chunk_num}: {e}")
            continue
        
        # Move to next chunk
        current_date = chunk_end
        chunk_num += 1
    
    # Convert to DataFrame
    if all_data:
        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        print(f"✅ Successfully extracted {len(df)} daily temperature records")
        return df
    else:
        print("❌ No data extracted")
        return pd.DataFrame()

def calculate_monthly_averages(daily_df):
    """Calculate monthly temperature averages"""
    if daily_df.empty:
        return pd.DataFrame()
    
    print("📊 Calculating monthly averages...")
    
    monthly_df = daily_df.copy()
    monthly_df['year_month'] = monthly_df['date'].dt.to_period('M')
    
    monthly_averages = monthly_df.groupby('year_month').agg({
        'tmax_celsius': ['mean', 'std', 'count'],
        'tmean_celsius': ['mean', 'std', 'count']
    }).round(2)
    
    # Flatten column names
    monthly_averages.columns = ['_'.join(col).strip() for col in monthly_averages.columns]
    monthly_averages = monthly_averages.reset_index()
    monthly_averages['date'] = monthly_averages['year_month'].dt.to_timestamp()
    
    print(f"✅ Calculated averages for {len(monthly_averages)} months")
    return monthly_averages

def export_data(daily_df, monthly_df, location_name, output_dir='data'):
    """Export data to CSV and Excel formats"""
    if daily_df.empty:
        print("❌ No data to export")
        return []
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Clean location name for filename
    clean_name = location_name.lower().replace(' ', '_').replace(',', '')
    
    # Get date range
    start_year = daily_df['date'].min().year
    end_year = daily_df['date'].max().year
    
    # Prepare data for export
    daily_export = daily_df[['date', 'tmax_celsius', 'tmean_celsius']].copy()
    
    # File paths
    daily_csv = os.path.join(output_dir, f"{clean_name}_daily_temp_{start_year}_{end_year}.csv")
    excel_file = os.path.join(output_dir, f"{clean_name}_temperature_data_{start_year}_{end_year}.xlsx")
    
    created_files = []
    
    try:
        # Export daily CSV
        daily_export.to_csv(daily_csv, index=False)
        created_files.append(daily_csv)
        print(f"✅ Exported daily data: {daily_csv}")
        
        # Export monthly CSV if available
        if not monthly_df.empty:
            monthly_export = monthly_df[['year_month', 'tmax_celsius_mean', 'tmean_celsius_mean']].copy()
            monthly_export.columns = ['month', 'avg_tmax_celsius', 'avg_tmean_celsius']
            monthly_csv = os.path.join(output_dir, f"{clean_name}_monthly_temp_{start_year}_{end_year}.csv")
            monthly_export.to_csv(monthly_csv, index=False)
            created_files.append(monthly_csv)
            print(f"✅ Exported monthly data: {monthly_csv}")
        
        # Export Excel file
        with pd.ExcelWriter(excel_file) as writer:
            daily_export.to_excel(writer, sheet_name='Daily_Data', index=False)
            if not monthly_df.empty:
                monthly_export.to_excel(writer, sheet_name='Monthly_Averages', index=False)
            
            # Add metadata
            metadata = pd.DataFrame({
                'Parameter': ['Location', 'Date Range', 'Daily Records', 'Data Source'],
                'Value': [location_name, 
                         f"{daily_df['date'].min().date()} to {daily_df['date'].max().date()}",
                         len(daily_export),
                         'ERA5-Land (ECMWF)']
            })
            metadata.to_excel(writer, sheet_name='Metadata', index=False)
        
        created_files.append(excel_file)
        print(f"✅ Exported Excel file: {excel_file}")
        
    except Exception as e:
        print(f"❌ Error exporting data: {e}")
    
    return created_files

def create_summary_plot(daily_df, monthly_df, location_name, save_plot=True):
    """Create summary visualization"""
    if daily_df.empty:
        print("❌ No data to plot")
        return
    
    print("📈 Creating summary visualization...")
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(f'Temperature Analysis: {location_name}', fontsize=16, fontweight='bold')
    
    # Daily time series
    axes[0, 0].plot(daily_df['date'], daily_df['tmax_celsius'], 'r-', alpha=0.6, linewidth=0.5, label='Daily Max')
    axes[0, 0].plot(daily_df['date'], daily_df['tmean_celsius'], 'b-', alpha=0.6, linewidth=0.5, label='Daily Mean')
    axes[0, 0].set_title('Daily Temperature Time Series')
    axes[0, 0].set_ylabel('Temperature (°C)')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Monthly averages (if available)
    if not monthly_df.empty:
        axes[0, 1].plot(monthly_df['date'], monthly_df['tmax_celsius_mean'], 'ro-', markersize=4, label='Monthly Avg Max')
        axes[0, 1].plot(monthly_df['date'], monthly_df['tmean_celsius_mean'], 'bo-', markersize=4, label='Monthly Avg Mean')
        axes[0, 1].set_title('Monthly Average Temperatures')
        axes[0, 1].set_ylabel('Temperature (°C)')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
    else:
        axes[0, 1].text(0.5, 0.5, 'No monthly data available', ha='center', va='center', transform=axes[0, 1].transAxes)
        axes[0, 1].set_title('Monthly Averages')
    
    # Temperature distribution
    axes[1, 0].hist(daily_df['tmax_celsius'], bins=30, alpha=0.7, color='red', label='Max Temp', density=True)
    axes[1, 0].hist(daily_df['tmean_celsius'], bins=30, alpha=0.7, color='blue', label='Mean Temp', density=True)
    axes[1, 0].set_title('Temperature Distribution')
    axes[1, 0].set_xlabel('Temperature (°C)')
    axes[1, 0].set_ylabel('Density')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # Basic statistics
    stats_text = f"""Daily Temperature Statistics:
    
Max Temperature:
  Mean: {daily_df['tmax_celsius'].mean():.1f}°C
  Range: {daily_df['tmax_celsius'].min():.1f}°C to {daily_df['tmax_celsius'].max():.1f}°C
  
Mean Temperature:  
  Mean: {daily_df['tmean_celsius'].mean():.1f}°C
  Range: {daily_df['tmean_celsius'].min():.1f}°C to {daily_df['tmean_celsius'].max():.1f}°C

Total Records: {len(daily_df)}
Date Range: {daily_df['date'].min().date()} to {daily_df['date'].max().date()}"""
    
    axes[1, 1].text(0.05, 0.95, stats_text, transform=axes[1, 1].transAxes, 
                    verticalalignment='top', fontfamily='monospace', fontsize=10)
    axes[1, 1].set_title('Summary Statistics')
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    
    if save_plot:
        plot_file = f"data/{location_name.lower().replace(' ', '_')}_temperature_analysis.png"
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        print(f"✅ Plot saved: {plot_file}")
    
    plt.show()

def main():
    """Main function to run the climate data extraction"""
    parser = argparse.ArgumentParser(description='Extract climate data for health research')
    parser.add_argument('--lat', type=float, default=-26.2678, help='Latitude (default: Soweto)')
    parser.add_argument('--lon', type=float, default=27.8607, help='Longitude (default: Soweto)')
    parser.add_argument('--location', type=str, default='Soweto, South Africa', help='Location name')
    parser.add_argument('--start-date', type=str, default='2016-04-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default='2022-03-31', help='End date (YYYY-MM-DD)')
    parser.add_argument('--buffer-km', type=float, default=10, help='Buffer radius in km')
    parser.add_argument('--chunk-days', type=int, default=90, help='Chunk size in days for processing')
    parser.add_argument('--no-plot', action='store_true', help='Skip creating plots')
    
    args = parser.parse_args()
    
    print("🌍 CLIMATE DATA EXTRACTION FOR HEALTH RESEARCH")
    print("=" * 60)
    print(f"Location: {args.location} ({args.lat}, {args.lon})")
    print(f"Date range: {args.start_date} to {args.end_date}")
    print(f"Buffer: {args.buffer_km} km")
    print("=" * 60)
    
    # Initialize Earth Engine
    if not initialize_earth_engine():
        sys.exit(1)
    
    # Create study area
    study_point, study_area = create_study_area(args.lat, args.lon, args.buffer_km)
    print(f"📍 Study area created with {args.buffer_km}km buffer")
    
    # Get climate data
    try:
        temperature_data = get_era5_temperature_data(study_area, args.start_date, args.end_date)
        
        # Extract time series in chunks
        daily_temps = extract_temperature_timeseries_chunked(
            temperature_data, study_point, args.start_date, args.end_date, args.chunk_days
        )
        
        if daily_temps.empty:
            print("❌ No temperature data extracted. Exiting.")
            sys.exit(1)
        
        # Calculate monthly averages
        monthly_temps = calculate_monthly_averages(daily_temps)
        
        # Export data
        created_files = export_data(daily_temps, monthly_temps, args.location)
        
        # Create visualization
        if not args.no_plot:
            create_summary_plot(daily_temps, monthly_temps, args.location)
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎉 EXTRACTION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"📊 Daily records: {len(daily_temps)}")
        if not monthly_temps.empty:
            print(f"📅 Monthly records: {len(monthly_temps)}")
        print(f"🌡️  Temperature range: {daily_temps['tmean_celsius'].min():.1f}°C to {daily_temps['tmean_celsius'].max():.1f}°C")
        
        if created_files:
            print("\n📁 Files created:")
            for file_path in created_files:
                print(f"   • {file_path}")
        
        print(f"\n💡 Next steps:")
        print(f"   • Import the CSV/Excel files into your health analysis software")
        print(f"   • Correlate monthly temperature averages with health outcomes")
        print(f"   • Consider temporal lags between climate and health effects")
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
