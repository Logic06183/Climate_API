"""
Command-line interface for Climate Toolkit.

Provides a user-friendly CLI for extracting and exporting climate data.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from . import __version__
from .core.extractor import ClimateDataExtractor
from .exporters.data_exporter import ClimateDataExporter
from .config import ClimateToolkitConfig, get_config
from .logger import setup_logger, get_logger


@click.group()
@click.version_option(version=__version__, prog_name="climate-toolkit")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration YAML file",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Logging level",
)
@click.pass_context
def cli(ctx: click.Context, config: Optional[Path], log_level: str) -> None:
    """
    Climate Toolkit - Extract climate data for health research.

    A professional toolkit for extracting climate data from Google Earth Engine
    for climate-health research applications.
    """
    # Load configuration
    if config:
        toolkit_config = ClimateToolkitConfig.from_yaml(config)
    else:
        toolkit_config = get_config()

    # Override log level if specified
    toolkit_config.logging.level = log_level.upper()

    # Setup logging
    setup_logger(config=toolkit_config.logging)

    # Store config in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["config"] = toolkit_config


@cli.command()
@click.option(
    "--lat",
    type=float,
    required=True,
    help="Latitude in decimal degrees",
)
@click.option(
    "--lon",
    type=float,
    required=True,
    help="Longitude in decimal degrees",
)
@click.option(
    "--start-date",
    type=str,
    required=True,
    help="Start date (YYYY-MM-DD)",
)
@click.option(
    "--end-date",
    type=str,
    required=True,
    help="End date (YYYY-MM-DD)",
)
@click.option(
    "--location",
    type=str,
    default="Study Location",
    help="Location name for output files",
)
@click.option(
    "--buffer-km",
    type=float,
    default=None,
    help="Buffer radius in kilometers (default: 10)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for exported files",
)
@click.option(
    "--no-monthly",
    is_flag=True,
    help="Skip monthly average calculations",
)
@click.option(
    "--no-export",
    is_flag=True,
    help="Skip exporting data files",
)
@click.option(
    "--no-plot",
    is_flag=True,
    help="Skip creating visualizations",
)
@click.option(
    "--project-id",
    type=str,
    default=None,
    help="Google Earth Engine project ID",
)
@click.pass_context
def extract(
    ctx: click.Context,
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    location: str,
    buffer_km: Optional[float],
    output_dir: Optional[Path],
    no_monthly: bool,
    no_export: bool,
    no_plot: bool,
    project_id: Optional[str],
) -> None:
    """
    Extract climate data for a specific location and time period.

    This command extracts temperature data from Google Earth Engine's ERA5-Land
    dataset for the specified location and date range.

    Example:

        \b
        climate-extract extract --lat -26.2678 --lon 27.8607 \\
            --start-date 2020-01-01 --end-date 2020-12-31 \\
            --location "Soweto, South Africa"
    """
    logger = get_logger()
    config = ctx.obj["config"]

    # Override project ID if provided
    if project_id:
        config.gee.project_id = project_id

    # Override output directory if provided
    if output_dir:
        config.output.output_dir = output_dir

    logger.info(f"Climate Toolkit v{__version__}")
    logger.info("=" * 60)
    logger.info(f"Extracting climate data for: {location}")
    logger.info(f"Location: ({lat}, {lon})")
    logger.info(f"Date range: {start_date} to {end_date}")
    logger.info("=" * 60)

    try:
        # Initialize extractor
        extractor = ClimateDataExtractor(config)

        # Extract data
        result = extractor.extract_climate_data(
            lat=lat,
            lon=lon,
            start_date=start_date,
            end_date=end_date,
            location_name=location,
            buffer_km=buffer_km,
            calculate_monthly=not no_monthly,
        )

        daily_df = result["daily"]
        monthly_df = result.get("monthly", None)

        # Print summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("EXTRACTION COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Daily records: {len(daily_df)}")
        if monthly_df is not None and not monthly_df.empty:
            logger.info(f"Monthly records: {len(monthly_df)}")
        logger.info(
            f"Temperature range: {daily_df['tmean_celsius'].min():.1f}°C "
            f"to {daily_df['tmean_celsius'].max():.1f}°C"
        )

        # Export data
        if not no_export:
            logger.info("")
            logger.info("Exporting data...")
            exporter = ClimateDataExporter(config.output)
            created_files = exporter.export_data(
                daily_df, monthly_df or pd.DataFrame(), location
            )

            if created_files:
                logger.info(f"Created {len(created_files)} file(s)")

        # Create visualization
        if not no_plot:
            logger.info("")
            logger.info("Creating visualization...")
            exporter = ClimateDataExporter(config.output)
            plot_file = exporter.create_visualization(
                daily_df, monthly_df or pd.DataFrame(), location
            )

        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        if config.logging.level == "DEBUG":
            import traceback

            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option(
    "--project-id",
    type=str,
    default=None,
    help="Google Earth Engine project ID to test",
)
@click.pass_context
def test_connection(ctx: click.Context, project_id: Optional[str]) -> None:
    """
    Test Google Earth Engine connection.

    Verifies that your Google Earth Engine credentials are properly configured
    and that you can access GEE datasets.
    """
    logger = get_logger()
    config = ctx.obj["config"]

    if project_id:
        config.gee.project_id = project_id

    logger.info("Testing Google Earth Engine connection...")
    logger.info("=" * 60)

    try:
        # Try to initialize extractor
        extractor = ClimateDataExtractor(config)

        # Try a simple query
        import ee

        collection = ee.ImageCollection("LANDSAT/LC08/C01/T1")
        count = collection.limit(1).size().getInfo()

        logger.info("✅ Google Earth Engine connection successful!")
        logger.info(f"✅ Basic query successful (found {count} image)")
        logger.info("=" * 60)
        logger.info("Your GEE setup is working correctly!")

    except Exception as e:
        logger.error("❌ Google Earth Engine connection failed")
        logger.error(f"Error: {e}")
        logger.info("")
        logger.info("Troubleshooting steps:")
        logger.info("  1. Run: earthengine authenticate --force")
        logger.info("  2. Ensure your Google Cloud project has Earth Engine enabled")
        logger.info("  3. Set GEE_PROJECT_ID environment variable")
        logger.info("  4. Visit: https://earthengine.google.com")
        sys.exit(1)


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="config.yaml",
    help="Output path for config file",
)
def init_config(output: Path) -> None:
    """
    Generate a sample configuration file.

    Creates a YAML configuration file with default settings that you can
    customize for your needs.
    """
    logger = get_logger()

    if output.exists():
        click.confirm(
            f"File {output} already exists. Overwrite?",
            abort=True,
        )

    config = ClimateToolkitConfig()
    config.save_yaml(output)

    logger.info(f"✅ Configuration file created: {output}")
    logger.info("Edit this file to customize your settings, then use:")
    logger.info(f"  climate-extract --config {output} extract ...")


def main() -> None:
    """Main entry point for CLI."""
    # Import pandas here to avoid circular import
    import pandas as pd

    cli(obj={})


if __name__ == "__main__":
    main()
