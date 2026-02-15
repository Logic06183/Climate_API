"""
Core climate data extraction functionality.

This module provides the main ClimateDataExtractor class that handles
all interactions with Google Earth Engine for extracting climate data.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import ee
import pandas as pd
import numpy as np

from ..config import ClimateToolkitConfig, get_config
from ..logger import LoggerMixin


class ClimateDataExtractor(LoggerMixin):
    """
    Main class for extracting climate data from Google Earth Engine.

    This class handles:
    - GEE initialization and authentication
    - Study area creation
    - Data extraction from various climate datasets
    - Chunked processing for large time series
    - Temperature unit conversions
    """

    def __init__(self, config: Optional[ClimateToolkitConfig] = None):
        """
        Initialize the Climate Data Extractor.

        Args:
            config: Configuration object (uses global config if None)
        """
        self.config = config or get_config()
        self.initialized = False
        self._initialize_gee()

    def _initialize_gee(self) -> None:
        """
        Initialize Google Earth Engine with proper error handling.

        Raises:
            RuntimeError: If GEE initialization fails
        """
        try:
            if self.config.gee.project_id:
                ee.Initialize(project=self.config.gee.project_id)
                self.logger.info(
                    f"Google Earth Engine initialized with project: {self.config.gee.project_id}"
                )
            else:
                ee.Initialize()
                self.logger.info("Google Earth Engine initialized (no project)")

            self.initialized = True

        except Exception as e:
            self.logger.error(f"Failed to initialize Google Earth Engine: {e}")
            self.logger.info(
                "Troubleshooting:\n"
                "  1. Run: earthengine authenticate --force\n"
                "  2. Ensure your Google Cloud project has Earth Engine enabled\n"
                "  3. Set GEE_PROJECT_ID environment variable"
            )
            raise RuntimeError(f"GEE initialization failed: {e}") from e

    def _check_initialized(self) -> None:
        """
        Check if GEE is initialized.

        Raises:
            RuntimeError: If GEE is not initialized
        """
        if not self.initialized:
            raise RuntimeError(
                "Google Earth Engine not initialized. "
                "Create a new ClimateDataExtractor instance."
            )

    def create_study_area(
        self, lat: float, lon: float, buffer_km: Optional[float] = None
    ) -> Tuple[ee.Geometry.Point, ee.Geometry]:
        """
        Create a study area geometry from coordinates.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            buffer_km: Buffer radius in kilometers (uses config default if None)

        Returns:
            Tuple of (point geometry, buffered area geometry)

        Raises:
            RuntimeError: If GEE is not initialized
            ValueError: If coordinates are invalid
        """
        self._check_initialized()

        # Validate coordinates
        if not (-90 <= lat <= 90):
            raise ValueError(f"Invalid latitude: {lat}. Must be between -90 and 90")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Invalid longitude: {lon}. Must be between -180 and 180")

        buffer_km = buffer_km or self.config.extraction.default_buffer_km

        point = ee.Geometry.Point([lon, lat])
        area = point.buffer(buffer_km * 1000)  # Convert km to meters

        self.logger.debug(
            f"Created study area at ({lat}, {lon}) with {buffer_km}km buffer"
        )

        return point, area

    def get_era5_temperature(
        self,
        geometry: ee.Geometry,
        start_date: str,
        end_date: str,
    ) -> ee.ImageCollection:
        """
        Get ERA5-Land temperature data for a geometry and time period.

        Args:
            geometry: Study area geometry
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Image collection with temperature data in Celsius

        Raises:
            RuntimeError: If GEE is not initialized
            ValueError: If date range is invalid
        """
        self._check_initialized()
        self._validate_date_range(start_date, end_date)

        self.logger.info(f"Loading ERA5 data from {start_date} to {end_date}")

        collection = (
            ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
            .filterDate(start_date, end_date)
            .filterBounds(geometry)
        )

        # Convert temperature from Kelvin to Celsius
        def convert_temperature(image: ee.Image) -> ee.Image:
            """Convert ERA5 temperature bands from Kelvin to Celsius."""
            t_mean = (
                image.select("temperature_2m")
                .subtract(273.15)
                .rename("temperature_2m_celsius")
            )
            t_max = (
                image.select("temperature_2m_max")
                .subtract(273.15)
                .rename("temperature_2m_max_celsius")
            )

            return (
                image.addBands([t_mean, t_max])
                .select(["temperature_2m_celsius", "temperature_2m_max_celsius"])
                .copyProperties(image, ["system:time_start"])
            )

        temperature_collection = collection.map(convert_temperature)

        count = temperature_collection.size().getInfo()
        self.logger.info(f"Found {count} daily temperature records")

        return temperature_collection

    def extract_timeseries_chunked(
        self,
        collection: ee.ImageCollection,
        point: ee.Geometry.Point,
        start_date: str,
        end_date: str,
        chunk_days: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Extract temperature time series in chunks to manage API limits.

        Args:
            collection: Image collection to extract from
            point: Point geometry for extraction
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            chunk_days: Chunk size in days (uses config default if None)

        Returns:
            DataFrame with daily temperature data

        Raises:
            RuntimeError: If extraction fails
        """
        self._check_initialized()

        chunk_days = chunk_days or self.config.extraction.default_chunk_days
        scale = self.config.extraction.default_scale_m

        self.logger.info(f"Extracting time series in {chunk_days}-day chunks")

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        all_data = []
        current_date = start_dt
        chunk_num = 1

        while current_date < end_dt:
            # Calculate chunk boundaries
            chunk_end = min(current_date + timedelta(days=chunk_days), end_dt)
            chunk_start_str = current_date.strftime("%Y-%m-%d")
            chunk_end_str = chunk_end.strftime("%Y-%m-%d")

            self.logger.debug(
                f"Processing chunk {chunk_num}: {chunk_start_str} to {chunk_end_str}"
            )

            try:
                # Filter collection for this chunk
                chunk_collection = collection.filterDate(chunk_start_str, chunk_end_str)

                # Extract data
                chunk_data = chunk_collection.getRegion(point, scale).getInfo()

                if len(chunk_data) > 1:  # Has data beyond header row
                    for row in chunk_data[1:]:
                        # Check for valid data (not None)
                        if row[4] is not None and row[5] is not None:
                            date_ms = row[3]
                            date_obj = datetime.fromtimestamp(date_ms / 1000)

                            all_data.append(
                                {
                                    "date": date_obj.date(),
                                    "tmax_celsius": row[4],
                                    "tmean_celsius": row[5],
                                }
                            )

                    self.logger.debug(
                        f"Chunk {chunk_num} completed: {len(chunk_data)-1} records"
                    )

            except Exception as e:
                self.logger.warning(f"Error processing chunk {chunk_num}: {e}")
                # Continue with next chunk rather than failing completely

            current_date = chunk_end
            chunk_num += 1

        if not all_data:
            raise RuntimeError("No data extracted. Check date range and location.")

        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        self.logger.info(f"Successfully extracted {len(df)} daily temperature records")
        return df

    def calculate_monthly_averages(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate monthly temperature averages from daily data.

        Args:
            daily_df: DataFrame with daily temperature data

        Returns:
            DataFrame with monthly averages and statistics
        """
        if daily_df.empty:
            self.logger.warning("No daily data provided for monthly averaging")
            return pd.DataFrame()

        self.logger.info("Calculating monthly averages")

        monthly_df = daily_df.copy()
        monthly_df["year_month"] = monthly_df["date"].dt.to_period("M")

        monthly_averages = (
            monthly_df.groupby("year_month")
            .agg(
                {
                    "tmax_celsius": ["mean", "std", "min", "max", "count"],
                    "tmean_celsius": ["mean", "std", "min", "max", "count"],
                }
            )
            .round(2)
        )

        # Flatten column names
        monthly_averages.columns = [
            "_".join(col).strip() for col in monthly_averages.columns
        ]
        monthly_averages = monthly_averages.reset_index()
        monthly_averages["date"] = monthly_averages["year_month"].dt.to_timestamp()

        self.logger.info(f"Calculated averages for {len(monthly_averages)} months")
        return monthly_averages

    def _validate_date_range(self, start_date: str, end_date: str) -> None:
        """
        Validate date range for data extraction.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Raises:
            ValueError: If date range is invalid
        """
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

            if end_dt <= start_dt:
                raise ValueError("End date must be after start date")

            if start_dt > datetime.now():
                raise ValueError("Start date cannot be in the future")

            # ERA5 data availability (starts from 1979)
            if start_dt < datetime(1979, 1, 1):
                raise ValueError("ERA5 data is only available from 1979-01-01")

        except ValueError as e:
            if "does not match format" in str(e):
                raise ValueError("Invalid date format. Use YYYY-MM-DD") from e
            raise

    def extract_climate_data(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        location_name: str = "Study Location",
        buffer_km: Optional[float] = None,
        calculate_monthly: bool = True,
    ) -> Dict[str, pd.DataFrame]:
        """
        Complete workflow to extract climate data for a location.

        This is a convenience method that combines all extraction steps.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            location_name: Name of the location (for logging/reporting)
            buffer_km: Buffer radius in kilometers
            calculate_monthly: Whether to calculate monthly averages

        Returns:
            Dictionary with 'daily' and 'monthly' DataFrames
        """
        self.logger.info(f"Extracting climate data for {location_name}")
        self.logger.info(f"Location: ({lat}, {lon})")
        self.logger.info(f"Date range: {start_date} to {end_date}")

        # Create study area
        study_point, study_area = self.create_study_area(lat, lon, buffer_km)

        # Get temperature data
        temperature_collection = self.get_era5_temperature(
            study_area, start_date, end_date
        )

        # Extract time series
        daily_df = self.extract_timeseries_chunked(
            temperature_collection, study_point, start_date, end_date
        )

        result = {"daily": daily_df}

        # Calculate monthly averages if requested
        if calculate_monthly:
            monthly_df = self.calculate_monthly_averages(daily_df)
            result["monthly"] = monthly_df
        else:
            result["monthly"] = pd.DataFrame()

        return result
