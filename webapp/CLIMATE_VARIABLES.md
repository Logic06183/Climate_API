# Climate Variables Implementation Guide

## Variables Added to UI

All variables sourced from **ERA5-Land Daily Aggregated** dataset (ECMWF):
https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land

### Available Variables:

1. **Temperature** ✅ (Currently Implemented)
   - Mean (temperature_2m)
   - Maximum (temperature_2m_max)
   - Minimum (temperature_2m_min)
   - Units: °C (converted from Kelvin)

2. **Precipitation** (Ready to implement)
   - Total daily precipitation
   - Band: `total_precipitation_sum`
   - Units: mm (converted from m)

3. **Humidity** (Ready to implement)
   - Dewpoint temperature at 2m
   - Band: `dewpoint_temperature_2m`
   - Units: °C (converted from Kelvin)

4. **Wind** (Ready to implement)
   - U component (eastward) at 10m
   - V component (northward) at 10m
   - Bands: `u_component_of_wind_10m`, `v_component_of_wind_10m`
   - Units: m/s
   - Can calculate wind speed: √(u² + v²)
   - Can calculate direction: atan2(v, u)

5. **Solar Radiation** (Ready to implement)
   - Surface solar radiation downwards
   - Band: `surface_solar_radiation_downwards_sum`
   - Units: J/m²

6. **Surface Pressure** (Ready to implement)
   - Surface air pressure
   - Band: `surface_pressure`
   - Units: Pa

7. **Evapotranspiration** (Ready to implement)
   - Potential evapotranspiration
   - Band: `potential_evaporation_sum`
   - Units: m (can convert to mm)

## Implementation Status

### ✅ Completed:
- UI checkboxes for variable selection (both single and batch modes)
- Source attribution with link to ERA5-Land dataset
- Temperature extraction fully working
- CSV batch processing working

### 🔄 To Complete:

1. **Update JavaScript** (`app.js`):
   - Collect selected variables from checkboxes
   - Send to backend in API requests

2. **Update Backend** (`main.py`):
   - Accept `variables` parameter in endpoints
   - Pass to climate extraction functions

3. **Update Climate Utils** (`climate_utils.py`):
   - Create new methods for each variable type
   - Add method to extract multiple variables at once
   - Return combined dataframe with all selected variables

4. **Update Response Formatting**:
   - Handle variable column names in Excel export
   - Update chart generation to show selected variables
   - Add metadata about data source to downloads

## ERA5-Land Band Names Reference

```python
VARIABLE_MAPPING = {
    'temperature': {
        'bands': ['temperature_2m', 'temperature_2m_max', 'temperature_2m_min'],
        'convert': lambda x: x - 273.15,  # Kelvin to Celsius
        'output_names': ['tmean_celsius', 'tmax_celsius', 'tmin_celsius']
    },
    'precipitation': {
        'bands': ['total_precipitation_sum'],
        'convert': lambda x: x * 1000,  # m to mm
        'output_names': ['precipitation_mm']
    },
    'humidity': {
        'bands': ['dewpoint_temperature_2m'],
        'convert': lambda x: x - 273.15,  # Kelvin to Celsius
        'output_names': ['dewpoint_celsius']
    },
    'wind': {
        'bands': ['u_component_of_wind_10m', 'v_component_of_wind_10m'],
        'convert': None,  # Already in m/s
        'output_names': ['wind_u_ms', 'wind_v_ms']
    },
    'solar': {
        'bands': ['surface_solar_radiation_downwards_sum'],
        'convert': None,  # Already in J/m²
        'output_names': ['solar_radiation_jm2']
    },
    'pressure': {
        'bands': ['surface_pressure'],
        'convert': None,  # Already in Pa
        'output_names': ['surface_pressure_pa']
    },
    'evapotranspiration': {
        'bands': ['potential_evaporation_sum'],
        'convert': lambda x: abs(x) * 1000,  # m to mm (take absolute value)
        'output_names': ['evapotranspiration_mm']
    }
}
```

## Data Citation

For scientific publications, users should cite:

> Muñoz Sabater, J., (2019): ERA5-Land hourly data from 1950 to present.
> Copernicus Climate Change Service (C3S) Climate Data Store (CDS).
> DOI: 10.24381/cds.e2161bac

## Health Research Applications

### Temperature:
- Heat stress studies
- Temperature-mortality relationships
- Seasonal disease patterns

### Precipitation:
- Vector-borne disease (mosquito breeding)
- Waterborne disease outbreaks
- Flooding health impacts

### Humidity:
- Respiratory disease transmission
- Heat index calculations
- Indoor air quality studies

### Wind:
- Air pollution dispersion
- Airborne disease transmission
- Wind chill effects

### Solar Radiation:
- UV exposure studies
- Vitamin D research
- Skin cancer risk

### Pressure:
- Cardiovascular event triggers
- Migraine studies
- Joint pain research

### Evapotranspiration:
- Drought health impacts
- Agricultural health linkages
- Water stress indicators
