#!/usr/bin/env python3
"""
Basic Climate Data Extraction Example

This example demonstrates how to use the Climate Toolkit library
to extract temperature data for a specific location.
"""

from climate_toolkit import ClimateDataExtractor, ClimateDataExporter
from climate_toolkit.config import ClimateToolkitConfig, GEEConfig
from climate_toolkit.logger import setup_logger

def main():
    """Extract climate data for Soweto, South Africa."""

    # Setup logging
    logger = setup_logger()

    # Configure the toolkit
    config = ClimateToolkitConfig(
        gee=GEEConfig(project_id="joburg-hvi")  # Replace with your project ID
    )

    # Initialize extractor
    logger.info("Initializing Climate Data Extractor...")
    extractor = ClimateDataExtractor(config)

    # Define study parameters
    location_name = "Soweto, South Africa"
    lat = -26.2678
    lon = 27.8607
    start_date = "2020-01-01"
    end_date = "2020-12-31"

    # Extract climate data
    logger.info(f"Extracting climate data for {location_name}...")
    result = extractor.extract_climate_data(
        lat=lat,
        lon=lon,
        start_date=start_date,
        end_date=end_date,
        location_name=location_name,
        buffer_km=10,  # 10km buffer around point
        calculate_monthly=True,
    )

    # Get the data
    daily_df = result["daily"]
    monthly_df = result["monthly"]

    # Display summary
    logger.info("\n" + "=" * 60)
    logger.info("EXTRACTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Daily records: {len(daily_df)}")
    logger.info(f"Monthly records: {len(monthly_df)}")
    logger.info(
        f"Temperature range: {daily_df['tmean_celsius'].min():.1f}°C "
        f"to {daily_df['tmax_celsius'].max():.1f}°C"
    )
    logger.info("=" * 60)

    # Preview data
    logger.info("\nFirst 5 daily records:")
    print(daily_df.head())

    logger.info("\nFirst 5 monthly records:")
    print(monthly_df.head())

    # Export data
    logger.info("\nExporting data...")
    exporter = ClimateDataExporter(config.output)

    created_files = exporter.export_data(
        daily_df=daily_df,
        monthly_df=monthly_df,
        location_name=location_name,
    )

    logger.info(f"\nCreated {len(created_files)} file(s):")
    for file_path in created_files:
        logger.info(f"  • {file_path}")

    # Create visualization
    logger.info("\nCreating visualization...")
    plot_file = exporter.create_visualization(
        daily_df=daily_df,
        monthly_df=monthly_df,
        location_name=location_name,
    )

    if plot_file:
        logger.info(f"Plot saved: {plot_file}")

    logger.info("\n✅ Completed successfully!")


if __name__ == "__main__":
    main()
