#!/usr/bin/env python3
"""
Multi-Location Climate Data Extraction Example

This example demonstrates how to extract climate data for multiple
locations and compare them.
"""

from climate_toolkit import ClimateDataExtractor, ClimateDataExporter
from climate_toolkit.config import ClimateToolkitConfig, GEEConfig
from climate_toolkit.logger import setup_logger

# Define study locations
LOCATIONS = [
    {"name": "Johannesburg, South Africa", "lat": -26.2041, "lon": 28.0473},
    {"name": "Cape Town, South Africa", "lat": -33.9249, "lon": 18.4241},
    {"name": "Durban, South Africa", "lat": -29.8587, "lon": 31.0218},
]


def main():
    """Extract climate data for multiple South African cities."""

    logger = setup_logger()

    # Configure the toolkit
    config = ClimateToolkitConfig(
        gee=GEEConfig(project_id="joburg-hvi")  # Replace with your project ID
    )

    # Initialize extractor
    extractor = ClimateDataExtractor(config)
    exporter = ClimateDataExporter(config.output)

    # Common parameters
    start_date = "2023-01-01"
    end_date = "2023-12-31"

    logger.info(f"Extracting climate data for {len(LOCATIONS)} locations")
    logger.info(f"Date range: {start_date} to {end_date}\n")

    results = {}

    # Extract data for each location
    for location in LOCATIONS:
        logger.info("=" * 60)
        logger.info(f"Processing: {location['name']}")
        logger.info("=" * 60)

        try:
            # Extract climate data
            result = extractor.extract_climate_data(
                lat=location["lat"],
                lon=location["lon"],
                start_date=start_date,
                end_date=end_date,
                location_name=location["name"],
                calculate_monthly=True,
            )

            results[location["name"]] = result

            # Export data for this location
            exporter.export_data(
                daily_df=result["daily"],
                monthly_df=result["monthly"],
                location_name=location["name"],
            )

            # Create visualization
            exporter.create_visualization(
                daily_df=result["daily"],
                monthly_df=result["monthly"],
                location_name=location["name"],
            )

            logger.info(f"✅ {location['name']} completed\n")

        except Exception as e:
            logger.error(f"❌ Error processing {location['name']}: {e}\n")
            continue

    # Compare results
    logger.info("\n" + "=" * 60)
    logger.info("COMPARISON SUMMARY")
    logger.info("=" * 60)

    for location_name, result in results.items():
        daily_df = result["daily"]
        logger.info(f"\n{location_name}:")
        logger.info(f"  Mean temperature: {daily_df['tmean_celsius'].mean():.1f}°C")
        logger.info(f"  Max temperature: {daily_df['tmax_celsius'].max():.1f}°C")
        logger.info(f"  Min temperature: {daily_df['tmean_celsius'].min():.1f}°C")

    logger.info("\n✅ All locations processed successfully!")


if __name__ == "__main__":
    main()
