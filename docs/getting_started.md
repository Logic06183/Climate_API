# Getting Started Guide

Welcome to the GEEMAP Climate Data for Health Analysis toolkit! This guide will help you set up your environment and start extracting climate data for your health research.

## Prerequisites

### 1. Python Environment
- Python 3.8 or higher
- Conda or pip package manager
- Jupyter Notebook or JupyterLab

### 2. Google Earth Engine Account
You'll need a Google Earth Engine account to access climate datasets:

1. Go to [Google Earth Engine](https://earthengine.google.com/)
2. Click "Get Started" and sign up with your Google account
3. Complete the registration process (may take 1-2 days for approval)
4. Once approved, you'll receive a confirmation email

## Installation

### Step 1: Clone the Repository
```bash
git clone <your-repository-url>
cd Climate_API
```

### Step 2: Install Dependencies
```bash
# Using pip
pip install -r requirements.txt

# OR using conda
conda install --file requirements.txt
```

### Step 3: Authenticate with Google Earth Engine
```bash
# Run this command in your terminal
earthengine authenticate
```

This will open a web browser where you'll need to:
1. Sign in with your Google account
2. Allow Earth Engine to access your account
3. Copy the authentication code back to your terminal

### Step 4: Test Your Setup
```python
import ee
ee.Initialize()
print("Google Earth Engine initialized successfully!")
```

## Quick Start Tutorial

### Option 1: Interactive Jupyter Notebooks
Start with our step-by-step tutorials:

1. **Basic Tutorial**: `notebooks/01_basic_temperature_extraction.ipynb`
   - Learn the fundamentals of climate data extraction
   - Extract temperature data for any location
   - Export data to CSV and Excel formats

2. **Case Study**: `notebooks/case_study_soweto.ipynb`
   - Real-world example using Soweto, South Africa
   - Comprehensive analysis for health research
   - Integration with health outcome data

### Option 2: Using the Utility Functions
```python
from src.climate_utils import ClimateDataExtractor

# Initialize the extractor
extractor = ClimateDataExtractor()

# Define your study area
study_area = extractor.create_study_area(
    lat=-26.2678,  # Soweto latitude
    lon=27.8607,   # Soweto longitude
    buffer_km=10   # 10km radius
)

# Get temperature data
temp_data = extractor.get_era5_temperature(
    geometry=study_area,
    start_date='2020-01-01',
    end_date='2022-12-31'
)

# Extract to DataFrame
daily_temps = extractor.extract_temperature_timeseries(
    collection=temp_data,
    point=study_area.centroid()
)
```

## Project Workflow

### 1. Define Your Research Question
- What health outcome are you studying?
- What climate variables might be relevant?
- What geographic area and time period?

### 2. Set Up Your Study Parameters
- **Location**: Coordinates or place name
- **Time Period**: Start and end dates
- **Spatial Scale**: Point location or area
- **Temporal Scale**: Daily, weekly, or monthly analysis

### 3. Extract Climate Data
- Use ERA5 reanalysis data for temperature
- Consider other datasets for precipitation, humidity, etc.
- Export data in formats suitable for your analysis software

### 4. Integrate with Health Data
- Match temporal resolution (daily/monthly)
- Account for time lags between climate and health outcomes
- Consider confounding factors

### 5. Analyze and Visualize
- Correlation analysis
- Time series analysis
- Seasonal decomposition
- Statistical modeling

## Common Locations and Coordinates

For quick reference, here are coordinates for major African cities:

| City | Country | Latitude | Longitude |
|------|---------|----------|-----------|
| Johannesburg | South Africa | -26.2041 | 28.0473 |
| Cape Town | South Africa | -33.9249 | 18.4241 |
| Nairobi | Kenya | -1.2864 | 36.8172 |
| Lagos | Nigeria | 6.5244 | 3.3792 |
| Accra | Ghana | 5.6037 | -0.1870 |
| Kampala | Uganda | 0.3476 | 32.5825 |

## Data Sources

### ERA5-Land Daily Aggregated
- **Dataset ID**: `ECMWF/ERA5_LAND/DAILY_AGGR`
- **Temporal Coverage**: 1979-present
- **Spatial Resolution**: ~11km
- **Variables**: Temperature, precipitation, wind, pressure
- **Update Frequency**: Daily (with 2-3 day lag)

### MODIS Land Surface Temperature
- **Dataset ID**: `MODIS/006/MOD11A1`
- **Temporal Coverage**: 2000-present
- **Spatial Resolution**: 1km
- **Variables**: Day/night land surface temperature
- **Update Frequency**: Daily

## Troubleshooting

### Common Issues

#### 1. "Earth Engine not initialized"
```bash
# Re-authenticate
earthengine authenticate

# In Python, try:
import ee
ee.Authenticate()
ee.Initialize()
```

#### 2. "Memory limit exceeded"
- Reduce the time period for your analysis
- Use smaller geographic areas
- Process data in chunks

#### 3. "No data returned"
- Check your coordinates (latitude/longitude order)
- Verify your date range
- Ensure your geometry is valid

#### 4. Slow data extraction
- Large time periods take longer
- Consider using cloud computing for big datasets
- Process monthly averages instead of daily data

### Getting Help

1. **Check the Documentation**: Start with our [API Reference](api_reference.md)
2. **Review Examples**: Look at the provided notebooks
3. **Google Earth Engine Guides**: [developers.google.com/earth-engine](https://developers.google.com/earth-engine)
4. **GEEMAP Documentation**: [geemap.org](https://geemap.org)
5. **Open an Issue**: Report bugs or request features in our repository

## Best Practices

### Data Quality
- Always validate your extracted data
- Check for missing values and outliers
- Compare with ground station data when possible
- Document your data sources and processing steps

### Reproducibility
- Save your code and parameters
- Use version control for your analysis
- Document your methodology
- Share your processed datasets

### Performance
- Start with small areas and short time periods
- Use appropriate spatial and temporal resolution
- Cache intermediate results
- Consider using Google Colab for heavy computations

## Next Steps

Once you're comfortable with the basics:

1. **Advanced Tutorials**: Explore time series analysis and statistical modeling
2. **Multiple Variables**: Extract precipitation, humidity, and other climate data
3. **Spatial Analysis**: Work with multiple locations or spatial patterns
4. **Integration**: Combine with other environmental and health datasets
5. **Visualization**: Create maps and publication-ready figures

## Example Research Questions

### Infectious Diseases
- How does temperature affect malaria transmission rates?
- What's the relationship between rainfall and cholera outbreaks?
- Do heat waves increase hospital admissions?

### Maternal Health
- How do temperature extremes affect preterm birth rates?
- What's the impact of seasonal variation on maternal outcomes?
- How does climate change affect pregnancy outcomes?

### Cardiovascular Health
- Do temperature fluctuations trigger heart attacks?
- How does heat stress affect vulnerable populations?
- What's the relationship between air quality and climate?

### Mental Health
- How do seasonal patterns affect depression rates?
- What's the impact of extreme weather on mental health services?
- How does climate change affect community well-being?

---

*Happy researching! Remember that good climate-health research requires careful attention to both the climate data and the health outcomes. Always consider confounding factors and collaborate with domain experts.*
