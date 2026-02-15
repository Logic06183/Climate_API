"""
Pytest configuration and shared fixtures.

Provides reusable test fixtures for climate data, images, and GEE mocking.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Sample test data directory
TEST_DATA_DIR = Path(__file__).parent / "fixtures" / "data"
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture
def sample_daily_climate_data():
    """
    Generate sample daily climate data for testing.

    Returns:
        pandas DataFrame with daily temperature data
    """
    dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')

    # Generate realistic-looking temperature data
    np.random.seed(42)
    base_temp = 20
    seasonal = 10 * np.sin(np.linspace(0, 2*np.pi, len(dates)))
    noise = np.random.normal(0, 2, len(dates))

    df = pd.DataFrame({
        'date': dates,
        'tmax_celsius': base_temp + seasonal + noise + 5,
        'tmean_celsius': base_temp + seasonal + noise,
    })

    return df


@pytest.fixture
def sample_monthly_climate_data():
    """Generate sample monthly climate data."""
    months = pd.period_range(start='2020-01', end='2020-12', freq='M')

    df = pd.DataFrame({
        'year_month': months,
        'tmax_celsius_mean': [25, 26, 24, 22, 18, 15, 14, 16, 19, 22, 24, 25],
        'tmean_celsius_mean': [20, 21, 19, 17, 13, 10, 9, 11, 14, 17, 19, 20],
    })
    df['date'] = df['year_month'].dt.to_timestamp()

    return df


@pytest.fixture
def sample_climate_data_with_gaps():
    """Generate climate data with missing dates for gap testing."""
    dates = pd.date_range(start='2020-01-01', end='2020-01-31', freq='D')

    # Remove some dates to create gaps
    dates_with_gaps = [d for i, d in enumerate(dates) if i not in [5, 6, 7, 15, 16]]

    df = pd.DataFrame({
        'date': pd.to_datetime(dates_with_gaps),
        'tmax_celsius': np.random.uniform(20, 30, len(dates_with_gaps)),
        'tmean_celsius': np.random.uniform(15, 25, len(dates_with_gaps)),
    })

    return df


@pytest.fixture
def sample_climate_data_with_outliers():
    """Generate climate data with outliers for validation testing."""
    dates = pd.date_range(start='2020-01-01', end='2020-01-31', freq='D')

    temps = np.random.uniform(15, 25, len(dates))
    # Add some outliers
    temps[5] = -100  # Too cold
    temps[15] = 100  # Too hot

    df = pd.DataFrame({
        'date': dates,
        'tmax_celsius': temps + 5,
        'tmean_celsius': temps,
    })

    return df


@pytest.fixture
def sample_satellite_image():
    """
    Generate sample multi-band satellite image for testing.

    Returns:
        numpy array of shape (4, 100, 100) representing 4-band image
    """
    np.random.seed(42)

    # Create 4-band image (similar to Landsat RGB + NIR)
    height, width = 100, 100
    image = np.random.randint(0, 255, (4, height, width), dtype=np.uint8)

    # Add some structure (a bright square in the center)
    image[:, 40:60, 40:60] = 200

    return image


@pytest.fixture
def mock_gee_image():
    """Mock Google Earth Engine Image object."""
    mock_image = MagicMock()
    mock_image.select.return_value = mock_image
    mock_image.subtract.return_value = mock_image
    mock_image.rename.return_value = mock_image
    mock_image.addBands.return_value = mock_image
    mock_image.copyProperties.return_value = mock_image

    return mock_image


@pytest.fixture
def mock_gee_collection():
    """Mock Google Earth Engine ImageCollection."""
    mock_collection = MagicMock()
    mock_collection.filterDate.return_value = mock_collection
    mock_collection.filterBounds.return_value = mock_collection
    mock_collection.map.return_value = mock_collection
    mock_collection.size.return_value.getInfo.return_value = 365

    # Mock getRegion for data extraction
    sample_data = [
        ['id', 'longitude', 'latitude', 'time', 'temp_max', 'temp_mean'],
    ]

    # Add 30 days of sample data
    base_time = datetime(2020, 1, 1).timestamp() * 1000
    for i in range(30):
        sample_data.append([
            f'image_{i}',
            27.8607,  # Soweto longitude
            -26.2678,  # Soweto latitude
            base_time + i * 86400000,  # milliseconds per day
            25.0 + np.random.normal(0, 2),  # tmax
            20.0 + np.random.normal(0, 2),  # tmean
        ])

    mock_collection.getRegion.return_value.getInfo.return_value = sample_data

    return mock_collection


@pytest.fixture
def mock_gee_geometry():
    """Mock Google Earth Engine Geometry."""
    mock_geometry = MagicMock()
    mock_point = MagicMock()
    mock_point.buffer.return_value = mock_geometry

    with patch('ee.Geometry.Point', return_value=mock_point):
        yield mock_point


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary directory for test outputs."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    from climate_toolkit.config import ClimateToolkitConfig, GEEConfig, ExtractionConfig

    config = ClimateToolkitConfig(
        gee=GEEConfig(project_id="test-project"),
        extraction=ExtractionConfig(
            default_buffer_km=5.0,
            default_chunk_days=30,
        )
    )

    return config


@pytest.fixture(autouse=True)
def mock_ee_initialize():
    """Automatically mock EE initialization for all tests."""
    with patch('ee.Initialize'):
        yield


@pytest.fixture
def sample_health_data():
    """Generate sample health data for integration testing."""
    dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='M')

    df = pd.DataFrame({
        'date': dates,
        'hospitalizations': np.random.poisson(100, len(dates)),
        'mortality_rate': np.random.uniform(0.5, 2.0, len(dates)),
    })

    return df
