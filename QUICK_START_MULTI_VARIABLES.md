# Quick Start Guide: Multi-Variable Climate Data Extraction

## Overview
Extract multiple climate variables (temperature, precipitation, humidity, wind, solar, pressure, evapotranspiration) from ERA5-Land data using Google Earth Engine.

## Installation
No changes needed - uses existing dependencies.

## Basic Usage

### 1. Import and Initialize
```python
from src.climate_utils import ClimateDataExtractor

# Initialize with your GEE project ID
extractor = ClimateDataExtractor(project_id='your-project-id')
```

### 2. Extract Single Variable
```python
# Define location and date range
lat, lon = -26.2041, 28.0473  # Johannesburg
start_date = "2023-01-01"
end_date = "2023-01-31"

# Create geometry
geometry = extractor.create_study_area(lat, lon, buffer_km=10)
point = extractor.create_point(lat, lon)

# Extract precipitation data
df = extractor.extract_climate_data(
    geometry=geometry,
    point=point,
    start_date=start_date,
    end_date=end_date,
    variables=['precipitation']
)

print(df.head())
```

### 3. Extract Multiple Variables
```python
# Extract temperature, precipitation, and wind
df = extractor.extract_climate_data(
    geometry=geometry,
    point=point,
    start_date=start_date,
    end_date=end_date,
    variables=['temperature', 'precipitation', 'wind']
)

print(df.columns)
# Output: ['date', 'tmax_celsius', 'tmean_celsius', 'precipitation_mm',
#          'wind_speed_ms', 'wind_u_ms', 'wind_v_ms']
```

### 4. Extract All Variables
```python
df = extractor.extract_climate_data(
    geometry=geometry,
    point=point,
    start_date=start_date,
    end_date=end_date,
    variables=[
        'temperature',
        'precipitation',
        'humidity',
        'wind',
        'solar',
        'pressure',
        'evapotranspiration'
    ]
)

# Save to CSV
df.to_csv('climate_data.csv', index=False)
```

## Available Variables

| Variable | Output Columns | Units | Description |
|----------|---------------|-------|-------------|
| `temperature` | `tmax_celsius`, `tmean_celsius` | °C | Daily maximum and mean temperature |
| `precipitation` | `precipitation_mm` | mm | Total daily precipitation |
| `humidity` | `dewpoint_celsius` | °C | Dewpoint temperature (humidity indicator) |
| `wind` | `wind_speed_ms`, `wind_u_ms`, `wind_v_ms` | m/s | Wind speed and components |
| `solar` | `solar_radiation_jm2` | J/m² | Surface solar radiation |
| `pressure` | `surface_pressure_pa` | Pa | Surface atmospheric pressure |
| `evapotranspiration` | `evapotranspiration_mm` | mm | Potential evapotranspiration |

## REST API Usage

### Extract via HTTP POST
```bash
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": -26.2041,
    "longitude": 28.0473,
    "location_name": "Johannesburg",
    "start_date": "2023-01-01",
    "end_date": "2023-01-31",
    "buffer_km": 10,
    "variables": ["temperature", "precipitation", "wind"]
  }'
```

### Response Format
```json
{
  "status": "success",
  "message": "Successfully extracted 31 records with 6 variables",
  "location": "Johannesburg",
  "records_extracted": 31,
  "temperature_range": {
    "temperature": {
      "min": 16.4,
      "max": 29.7,
      "mean": 22.8
    },
    "precipitation": {
      "total": 95.3,
      "mean": 3.1,
      "max": 28.7
    },
    "wind_speed": {
      "mean": 2.1,
      "max": 4.8
    }
  },
  "data": {
    "daily": [
      {
        "date": "2023-01-01",
        "tmax_celsius": 21.26,
        "tmean_celsius": 16.41,
        "precipitation_mm": 6.82,
        "wind_speed_ms": 1.13,
        "wind_u_ms": -0.23,
        "wind_v_ms": -1.11
      },
      ...
    ]
  }
}
```

## Common Use Cases

### Health Research: Disease Surveillance
```python
# Extract variables relevant to vector-borne diseases
df = extractor.extract_climate_data(
    geometry=geometry,
    point=point,
    start_date="2023-12-01",
    end_date="2024-02-29",
    variables=['temperature', 'precipitation', 'humidity']
)

# Identify high-risk periods
df['high_risk'] = (
    (df['tmean_celsius'] > 25) &
    (df['precipitation_mm'] > 1) &
    (df['dewpoint_celsius'] > 15)
)
```

### Agriculture: Crop Planning
```python
# Extract variables for crop water requirements
df = extractor.extract_climate_data(
    geometry=geometry,
    point=point,
    start_date="2023-01-01",
    end_date="2023-12-31",
    variables=['temperature', 'precipitation', 'evapotranspiration', 'solar']
)

# Calculate water balance
df['water_balance'] = df['precipitation_mm'] - df['evapotranspiration_mm']
```

### Climate Analysis: Heat Stress
```python
# Extract variables for heat stress assessment
df = extractor.extract_climate_data(
    geometry=geometry,
    point=point,
    start_date="2023-01-01",
    end_date="2023-12-31",
    variables=['temperature', 'humidity', 'wind']
)

# Calculate heat index (simplified)
df['heat_stress'] = df['tmax_celsius'] + 0.5 * df['dewpoint_celsius']
```

## Output Format

### CSV Structure
```csv
date,tmax_celsius,tmean_celsius,precipitation_mm,dewpoint_celsius,wind_speed_ms,...
2023-01-01,21.26,16.41,6.82,13.82,1.13,...
2023-01-02,22.71,18.04,0.50,11.65,0.79,...
2023-01-03,23.85,19.10,0.79,12.55,1.62,...
```

### DataFrame Info
```python
print(df.dtypes)
# Output:
# date                     datetime64[ns]
# tmax_celsius             float64
# tmean_celsius            float64
# precipitation_mm         float64
# dewpoint_celsius         float64
# wind_speed_ms            float64
# ...
```

## Error Handling

### Check Initialization
```python
if not extractor.initialized:
    print("Google Earth Engine not initialized")
    print("Run: earthengine authenticate")
```

### Handle Empty Results
```python
df = extractor.extract_climate_data(...)

if df.empty:
    print("No data found for specified period")
else:
    print(f"Successfully extracted {len(df)} records")
```

## Performance Tips

1. **Extract only needed variables** - faster extraction
   ```python
   variables=['temperature']  # Fast
   variables=['temperature', 'precipitation', 'humidity', ...]  # Slower
   ```

2. **Reasonable date ranges** - avoid very long periods
   ```python
   # Good: One month
   start_date="2023-01-01"
   end_date="2023-01-31"

   # OK: One year
   start_date="2023-01-01"
   end_date="2023-12-31"

   # Slow: Many years
   start_date="2000-01-01"
   end_date="2023-12-31"  # Use with caution
   ```

3. **Appropriate buffer size** - larger buffers = slower
   ```python
   buffer_km=10   # Fast - point data
   buffer_km=50   # Medium - small area average
   buffer_km=100  # Slower - large area average
   ```

## Backward Compatibility

Old temperature extraction method still works:
```python
# OLD METHOD (still works)
collection = extractor.get_era5_temperature(geometry, start_date, end_date)
df = extractor.extract_temperature_timeseries(collection, point)

# NEW METHOD (recommended)
df = extractor.extract_climate_data(
    geometry, point, start_date, end_date,
    variables=['temperature']
)

# Both produce identical results!
```

## Testing

Run comprehensive tests:
```bash
# Test all variables individually
python test_multi_variables.py

# Test backward compatibility
python test_backward_compatibility.py

# Test real-world scenario
python test_real_world_scenario.py
```

## Examples

See complete examples in:
- `example_multi_variable_usage.py` - Basic usage examples
- `test_real_world_scenario.py` - Health research scenario
- `test_multi_variables.py` - Comprehensive testing

## Troubleshooting

### "Google Earth Engine not initialized"
```bash
earthengine authenticate
```

### "No data found for specified period"
- Check date range (ERA5 starts from 1979-01-01)
- Verify coordinates are valid
- Ensure dates are in format YYYY-MM-DD

### "The column label 'date' is not unique"
- Update to latest version of climate_utils.py
- This issue was fixed in the current version

## Support

For questions or issues:
1. Check the documentation: `MULTI_VARIABLE_IMPLEMENTATION_SUMMARY.md`
2. Review test scripts for examples
3. Verify Google Earth Engine authentication

## Version
- Implementation Date: December 4, 2025
- ERA5-Land Dataset: ECMWF/ERA5_LAND/DAILY_AGGR
- All tests passing: 11/11
