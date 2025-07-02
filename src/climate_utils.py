"""
Climate Data Utilities for Health Research

This module provides utility functions for extracting and processing climate data
using Google Earth Engine for health research applications.

Author: Climate-Health Research Team
"""

import ee
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')


class ClimateDataExtractor:
    """
    A class for extracting climate data from Google Earth Engine
    """
    
    def __init__(self):
        """Initialize the climate data extractor"""
        self.initialized = False
        self._initialize_ee()
    
    def _initialize_ee(self):
        """Initialize Google Earth Engine"""
        try:
            ee.Initialize()
            self.initialized = True
            print("✅ Google Earth Engine initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing Google Earth Engine: {e}")
            print("Please run 'earthengine authenticate' in your terminal")
            self.initialized = False
    
    def create_study_area(self, lat: float, lon: float, buffer_km: float = 10) -> ee.Geometry:
        """
        Create a study area geometry from coordinates
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            buffer_km (float): Buffer radius in kilometers
            
        Returns:
            ee.Geometry: Study area geometry
        """
        if not self.initialized:
            raise RuntimeError("Google Earth Engine not initialized")
        
        point = ee.Geometry.Point([lon, lat])
        area = point.buffer(buffer_km * 1000)  # Convert km to meters
        return area
    
    def get_era5_temperature(self, geometry: ee.Geometry, start_date: str, 
                           end_date: str) -> ee.ImageCollection:
        """
        Get ERA5 temperature data for a geometry and time period
        
        Args:
            geometry (ee.Geometry): Study area geometry
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            ee.ImageCollection: Temperature data collection
        """
        if not self.initialized:
            raise RuntimeError("Google Earth Engine not initialized")
        
        collection = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR') \
            .filterDate(start_date, end_date) \
            .filterBounds(geometry)
        
        # Convert temperature from Kelvin to Celsius
        def convert_temp(image):
            temp_c = image.select(['temperature_2m_max', 'temperature_2m_mean']) \
                .subtract(273.15) \
                .copyProperties(image, ['system:time_start'])
            
            return temp_c.select(
                ['temperature_2m_max', 'temperature_2m_mean'],
                ['tmax_celsius', 'tmean_celsius']
            )
        
        return collection.map(convert_temp)
    
    def extract_temperature_timeseries(self, collection: ee.ImageCollection,
                                     point: ee.Geometry, scale: int = 1000) -> pd.DataFrame:
        """
        Extract temperature time series to pandas DataFrame
        
        Args:
            collection (ee.ImageCollection): Temperature data collection
            point (ee.Geometry): Point geometry for extraction
            scale (int): Scale in meters for extraction
            
        Returns:
            pd.DataFrame: Daily temperature data
        """
        if not self.initialized:
            raise RuntimeError("Google Earth Engine not initialized")
        
        print("🔄 Extracting temperature time series...")
        
        # Get the time series data
        time_series = collection.getRegion(point, scale).getInfo()
        
        # Convert to DataFrame
        header = time_series[0]
        data_rows = time_series[1:]
        
        df = pd.DataFrame(data_rows, columns=header)
        
        # Process datetime
        df['datetime'] = pd.to_datetime(df['time'], unit='ms')
        df['date'] = df['datetime'].dt.date
        
        # Clean and organize data
        temp_df = df[['date', 'tmax_celsius', 'tmean_celsius']].copy()
        temp_df = temp_df.dropna()
        temp_df = temp_df.sort_values('date').reset_index(drop=True)
        temp_df['date'] = pd.to_datetime(temp_df['date'])
        
        print(f"✅ Extracted {len(temp_df)} daily temperature records")
        return temp_df
    
    def calculate_monthly_averages(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate monthly temperature averages
        
        Args:
            daily_df (pd.DataFrame): Daily temperature data
            
        Returns:
            pd.DataFrame: Monthly averages
        """
        monthly_df = daily_df.copy()
        monthly_df['year_month'] = monthly_df['date'].dt.to_period('M')
        
        monthly_averages = monthly_df.groupby('year_month').agg({
            'tmax_celsius': ['mean', 'std', 'min', 'max', 'count'],
            'tmean_celsius': ['mean', 'std', 'min', 'max', 'count']
        }).round(2)
        
        # Flatten column names
        monthly_averages.columns = ['_'.join(col).strip() for col in monthly_averages.columns]
        monthly_averages = monthly_averages.reset_index()
        monthly_averages['date'] = monthly_averages['year_month'].dt.to_timestamp()
        
        return monthly_averages


def get_country_coordinates() -> Dict[str, Tuple[float, float]]:
    """
    Get coordinates for major cities/countries for quick reference
    
    Returns:
        Dict: Dictionary of location names and coordinates
    """
    return {
        'johannesburg_za': (-26.2041, 28.0473),
        'cape_town_za': (-33.9249, 18.4241),
        'durban_za': (-29.8587, 31.0218),
        'nairobi_ke': (-1.2864, 36.8172),
        'lagos_ng': (6.5244, 3.3792),
        'accra_gh': (5.6037, -0.1870),
        'kampala_ug': (0.3476, 32.5825),
        'dar_es_salaam_tz': (-6.7924, 39.2083),
        'harare_zw': (-17.8292, 31.0522),
        'lusaka_zm': (-15.3875, 28.3228)
    }


def validate_date_range(start_date: str, end_date: str) -> bool:
    """
    Validate date range for data extraction
    
    Args:
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        
    Returns:
        bool: True if valid date range
    """
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Check if end date is after start date
        if end_dt <= start_dt:
            print("❌ End date must be after start date")
            return False
        
        # Check if dates are not too far in the future
        if start_dt > datetime.now():
            print("❌ Start date cannot be in the future")
            return False
        
        # ERA5 data availability check (starts from 1979)
        if start_dt < datetime(1979, 1, 1):
            print("❌ ERA5 data is only available from 1979-01-01")
            return False
        
        return True
        
    except ValueError:
        print("❌ Invalid date format. Use YYYY-MM-DD")
        return False


def export_climate_data(daily_df: pd.DataFrame, monthly_df: pd.DataFrame,
                       location_name: str, output_dir: str = '../data') -> List[str]:
    """
    Export climate data to multiple formats
    
    Args:
        daily_df (pd.DataFrame): Daily temperature data
        monthly_df (pd.DataFrame): Monthly temperature data
        location_name (str): Name of the location
        output_dir (str): Output directory
        
    Returns:
        List[str]: List of created file paths
    """
    import os
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Clean location name for filename
    clean_name = location_name.lower().replace(' ', '_').replace(',', '')
    
    # Get date range
    start_year = daily_df['date'].min().year
    end_year = daily_df['date'].max().year
    
    # Prepare data for export
    daily_export = daily_df[['date', 'tmax_celsius', 'tmean_celsius']].copy()
    
    # Prepare monthly data
    if 'tmax_celsius_mean' in monthly_df.columns:
        monthly_export = monthly_df[['year_month', 'tmax_celsius_mean', 'tmean_celsius_mean']].copy()
        monthly_export.columns = ['month', 'avg_tmax_celsius', 'avg_tmean_celsius']
    else:
        monthly_export = monthly_df.copy()
    
    # File paths
    daily_csv = f"{output_dir}/{clean_name}_daily_temp_{start_year}_{end_year}.csv"
    monthly_csv = f"{output_dir}/{clean_name}_monthly_temp_{start_year}_{end_year}.csv"
    excel_file = f"{output_dir}/{clean_name}_temperature_data_{start_year}_{end_year}.xlsx"
    
    # Export CSV files
    daily_export.to_csv(daily_csv, index=False)
    monthly_export.to_csv(monthly_csv, index=False)
    
    # Export Excel file
    with pd.ExcelWriter(excel_file) as writer:
        daily_export.to_excel(writer, sheet_name='Daily_Data', index=False)
        monthly_export.to_excel(writer, sheet_name='Monthly_Averages', index=False)
        
        # Add metadata sheet
        metadata = pd.DataFrame({
            'Parameter': ['Location', 'Date Range', 'Daily Records', 'Monthly Records', 
                         'Min Temperature', 'Max Temperature', 'Data Source'],
            'Value': [location_name, 
                     f"{daily_df['date'].min().date()} to {daily_df['date'].max().date()}",
                     len(daily_export), len(monthly_export),
                     f"{daily_df['tmean_celsius'].min():.1f}°C",
                     f"{daily_df['tmax_celsius'].max():.1f}°C",
                     'ERA5-Land (ECMWF)']
        })
        metadata.to_excel(writer, sheet_name='Metadata', index=False)
    
    created_files = [daily_csv, monthly_csv, excel_file]
    
    print("💾 Data exported successfully!")
    print(f"📁 Files created:")
    for file_path in created_files:
        print(f"   • {file_path}")
    
    return created_files


def calculate_climate_health_correlation(climate_df: pd.DataFrame, 
                                       health_df: pd.DataFrame,
                                       climate_col: str = 'tmean_celsius',
                                       health_col: str = 'outcome_rate') -> Dict:
    """
    Calculate correlation between climate and health data
    
    Args:
        climate_df (pd.DataFrame): Climate data with date column
        health_df (pd.DataFrame): Health data with date column
        climate_col (str): Climate variable column name
        health_col (str): Health outcome column name
        
    Returns:
        Dict: Correlation results and statistics
    """
    # Merge datasets on date
    merged_df = pd.merge(climate_df, health_df, on='date', how='inner')
    
    if len(merged_df) == 0:
        return {'error': 'No matching dates between climate and health data'}
    
    # Calculate correlations
    pearson_r = merged_df[climate_col].corr(merged_df[health_col])
    spearman_r = merged_df[climate_col].corr(merged_df[health_col], method='spearman')
    
    # Basic statistics
    results = {
        'n_observations': len(merged_df),
        'pearson_correlation': round(pearson_r, 3),
        'spearman_correlation': round(spearman_r, 3),
        'climate_mean': round(merged_df[climate_col].mean(), 2),
        'climate_std': round(merged_df[climate_col].std(), 2),
        'health_mean': round(merged_df[health_col].mean(), 3),
        'health_std': round(merged_df[health_col].std(), 3),
        'date_range': f"{merged_df['date'].min().date()} to {merged_df['date'].max().date()}"
    }
    
    return results


def print_data_summary(df: pd.DataFrame, data_type: str = "Climate Data"):
    """
    Print a formatted summary of the dataset
    
    Args:
        df (pd.DataFrame): Dataset to summarize
        data_type (str): Type of data for display
    """
    print(f"\n📊 {data_type.upper()} SUMMARY")
    print("=" * 50)
    print(f"Total records: {len(df)}")
    
    if 'date' in df.columns:
        print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        duration_days = (df['date'].max() - df['date'].min()).days
        print(f"Duration: {duration_days} days ({duration_days/365.25:.1f} years)")
    
    # Numeric column summaries
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        print("\nNumeric variables:")
        for col in numeric_cols:
            if 'celsius' in col.lower() or 'temp' in col.lower():
                print(f"  {col}: {df[col].mean():.1f}°C ± {df[col].std():.1f}°C "
                      f"(range: {df[col].min():.1f}°C to {df[col].max():.1f}°C)")
            else:
                print(f"  {col}: {df[col].mean():.3f} ± {df[col].std():.3f} "
                      f"(range: {df[col].min():.3f} to {df[col].max():.3f})")
