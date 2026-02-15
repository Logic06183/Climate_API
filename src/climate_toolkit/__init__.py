"""
Climate Toolkit - Climate Data Extraction for Health Research

A professional toolkit for extracting and analyzing climate data using
Google Earth Engine (GEE) and GEEMAP, designed specifically for health
research applications.
"""

__version__ = "0.2.0"
__author__ = "Heat Centre Research Team"
__email__ = "research@heatcentre.org"

from .core.extractor import ClimateDataExtractor
from .exporters.data_exporter import ClimateDataExporter
from .config import ClimateToolkitConfig, get_config, set_config
from .logger import setup_logger, get_logger
from .health import ClimateHealthIntegrator

__all__ = [
    "ClimateDataExtractor",
    "ClimateDataExporter",
    "ClimateHealthIntegrator",
    "ClimateToolkitConfig",
    "get_config",
    "set_config",
    "setup_logger",
    "get_logger",
    "__version__",
]
