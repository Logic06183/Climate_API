# Climate-Health Intelligence Platform - Unified Architecture

## 🎯 Vision

A comprehensive platform integrating climate data extraction with AI-powered geospatial analysis for climate-health research.

## 🏗️ Architecture Overview

```
climate_health_platform/
├── extraction/          # Climate data extraction (from Climate_API)
│   ├── extractor.py    # ClimateDataExtractor
│   └── sources/        # Data source plugins (ERA5, MODIS, CHIRPS)
│
├── analysis/           # AI-powered image analysis (from geoAI)
│   ├── image_explorer.py    # Interactive image exploration
│   ├── segmentation.py      # AI segmentation (SAM, K-means)
│   └── indices.py           # Climate indices (NDVI, LST, HVI)
│
├── geospatial/         # Geospatial operations
│   ├── geo_utils.py    # CRS, reprojection, clipping
│   └── spatial_ops.py  # Spatial statistics, zonal stats
│
├── workflows/          # Integrated analysis workflows
│   ├── hvi_pipeline.py      # Heat Vulnerability Index
│   ├── extract_analyze.py   # Extract → Analyze workflow
│   └── health_integration.py # Climate-health correlation
│
├── exporters/          # Data export
│   ├── data_exporter.py    # CSV, Excel, GeoTIFF
│   └── visualizer.py       # Plots, maps, dashboards
│
├── core/               # Shared infrastructure
│   ├── config.py       # Unified configuration
│   ├── logger.py       # Logging framework
│   ├── cache.py        # Caching layer
│   └── validators.py   # Data quality checks
│
└── cli/                # Command-line interface
    ├── extract.py      # Extract commands
    ├── analyze.py      # Analysis commands
    └── workflows.py    # Workflow commands
```

## 🔄 Integration Workflows

### Workflow 1: Heat Vulnerability Index (HVI)
```
Extract LST & NDVI → Calculate HVI → Create Risk Maps → Export Results
```

### Workflow 2: Climate-Health Correlation
```
Extract Climate Data → Merge Health Data → Statistical Analysis → Visualize
```

### Workflow 3: Urban Heat Analysis
```
Download Satellite → Segment Urban Areas → Calculate Heat Islands → Risk Assessment
```

## 🎨 Design Principles

1. **Modularity**: Each component is independent and testable
2. **Configuration-driven**: All settings via YAML/env vars
3. **Type-safe**: Comprehensive type hints
4. **Tested**: >80% code coverage
5. **Cached**: Intelligent caching to respect API quotas
6. **Progressive**: Progress bars for long operations
7. **Validated**: Data quality checks at each stage
8. **Documented**: Comprehensive docs and examples

## 🧪 Testing Strategy

### Unit Tests
- Each module has dedicated test file
- Mock external dependencies (GEE, file I/O)
- Test edge cases and error handling

### Integration Tests
- Test workflow combinations
- Validate end-to-end pipelines
- Performance benchmarks

### Fixtures
- Sample satellite imagery
- Mock GEE responses
- Test climate datasets
- Example health data

## 📦 Dependencies

### Core
- earthengine-api, pandas, numpy, pyyaml, python-dotenv, click

### Geospatial
- rasterio, geopandas, shapely, folium

### Analysis
- scikit-learn, opencv-python, scikit-image, torch

### Visualization
- matplotlib, plotly, seaborn

### Development
- pytest, pytest-cov, pytest-mock, black, mypy, flake8

## 🚀 Usage Patterns

### CLI Usage
```bash
# Extract and analyze in one command
climate-health extract-and-analyze \
    --lat -26.2678 --lon 27.8607 \
    --start-date 2020-01-01 --end-date 2020-12-31 \
    --analysis hvi \
    --output ./results

# Just extract
climate-health extract [options]

# Just analyze existing data
climate-health analyze --input data.tif --method hvi

# Run complete HVI workflow
climate-health workflow hvi --location johannesburg
```

### Python API Usage
```python
from climate_health_platform import ClimateHealthPipeline

# Unified workflow
pipeline = ClimateHealthPipeline()
result = pipeline.run_hvi_analysis(
    location="Johannesburg",
    start_date="2020-01-01",
    end_date="2020-12-31"
)

# Or use components separately
from climate_health_platform.extraction import ClimateDataExtractor
from climate_health_platform.analysis import HVICalculator

extractor = ClimateDataExtractor()
data = extractor.extract_lst_and_ndvi(...)

hvi_calc = HVICalculator()
hvi_result = hvi_calc.calculate(data)
```

## 🔧 Advanced Features

### 1. Intelligent Caching
```python
# Cache expensive operations
@cache_to_disk(expire_hours=24)
def extract_climate_data(...):
    # Results cached for 24 hours
```

### 2. Progress Tracking
```python
# Automatic progress bars
with progress_tracker("Extracting data") as tracker:
    for chunk in chunks:
        process(chunk)
        tracker.update()
```

### 3. Data Quality Validation
```python
# Automatic quality checks
validator = DataQualityValidator()
validator.check_gaps(data)
validator.check_outliers(data)
validator.check_completeness(data)
```

### 4. Health Data Integration
```python
# Merge climate and health data with lags
merger = HealthDataMerger()
merged = merger.merge_with_lags(
    climate_df, health_df,
    lag_days=[0, 7, 14, 30]
)
```

## 📊 Data Flow

```
┌─────────────────┐
│ Google Earth    │
│ Engine (GEE)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Climate Data    │────▶│ Cache Layer     │
│ Extractor       │     └────────┬────────┘
└────────┬────────┘              │
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ Data Validator  │────▶│ Quality Report  │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ AI Analysis     │────▶│ Results Cache   │
│ (HVI, NDVI)     │     └─────────────────┘
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Visualization   │────▶│ Export          │
│ & Mapping       │     │ (CSV, GeoTIFF)  │
└─────────────────┘     └─────────────────┘
```

## 🎓 Key Improvements Over Original

1. **Unified Configuration**: Single config for both subsystems
2. **Shared Logging**: Consistent logging across all modules
3. **Type Safety**: Complete type hints for better IDE support
4. **Comprehensive Testing**: >80% coverage with pytest
5. **Performance**: Caching + parallel processing
6. **User Experience**: Progress bars, better error messages
7. **Integration**: Seamless workflows combining extraction + analysis
8. **Extensibility**: Plugin architecture for new data sources
9. **Documentation**: Complete API docs + examples
10. **Production Ready**: Error handling, retries, validation

## 🔐 Security & Best Practices

- Never commit credentials (use .env)
- Validate all user inputs
- Sanitize file paths
- Rate limit API calls
- Handle network failures gracefully
- Log security events
- Use secure temp file handling
