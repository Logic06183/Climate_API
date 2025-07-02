# Climate Data Sources for Health Research

This document provides detailed information about the climate datasets available through Google Earth Engine for health research applications.

## Primary Datasets

### 1. ERA5-Land Daily Aggregated (Recommended)

**Dataset ID**: `ECMWF/ERA5_LAND/DAILY_AGGR`

**Overview**: ERA5-Land is a state-of-the-art global reanalysis dataset providing consistent, high-quality meteorological data. It's particularly suitable for health research due to its comprehensive coverage and temporal consistency.

**Key Specifications**:
- **Temporal Coverage**: 1981-01-01 to present
- **Spatial Resolution**: 0.1° × 0.1° (~11 km)
- **Temporal Resolution**: Daily aggregations
- **Update Frequency**: Daily (with 2-3 day lag)
- **Data Provider**: European Centre for Medium-Range Weather Forecasts (ECMWF)

**Available Variables**:
- `temperature_2m_max`: Daily maximum temperature at 2m height (K)
- `temperature_2m_mean`: Daily mean temperature at 2m height (K)
- `temperature_2m_min`: Daily minimum temperature at 2m height (K)
- `total_precipitation_sum`: Daily total precipitation (m)
- `surface_pressure`: Surface pressure (Pa)
- `u_component_of_wind_10m`: U-component of wind at 10m (m/s)
- `v_component_of_wind_10m`: V-component of wind at 10m (m/s)

**Health Research Applications**:
- Temperature-health outcome relationships
- Seasonal disease pattern analysis
- Climate change impact assessments
- Heat wave and cold spell analysis

**Usage Example**:
```python
# Load ERA5-Land daily data
era5 = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR') \
    .filterDate('2020-01-01', '2022-12-31') \
    .filterBounds(study_area)

# Convert temperature from Kelvin to Celsius
def kelvin_to_celsius(image):
    return image.select(['temperature_2m_max', 'temperature_2m_mean']) \
        .subtract(273.15) \
        .copyProperties(image, ['system:time_start'])

temp_data = era5.map(kelvin_to_celsius)
```

**Quality and Limitations**:
- ✅ High quality, extensively validated
- ✅ Global coverage with consistent methodology
- ✅ Long temporal record suitable for trend analysis
- ⚠️ Spatial resolution may not capture very local variations
- ⚠️ Reanalysis data (modeled, not directly observed)

---

### 2. MODIS Land Surface Temperature

**Dataset ID**: `MODIS/006/MOD11A1` (Terra) / `MODIS/006/MYD11A1` (Aqua)

**Overview**: MODIS provides satellite-derived land surface temperature measurements with high spatial resolution, ideal for urban heat island studies and fine-scale temperature analysis.

**Key Specifications**:
- **Temporal Coverage**: 2000-02-24 to present
- **Spatial Resolution**: 1 km
- **Temporal Resolution**: Daily
- **Update Frequency**: Daily
- **Data Provider**: NASA

**Available Variables**:
- `LST_Day_1km`: Daytime land surface temperature (K)
- `LST_Night_1km`: Nighttime land surface temperature (K)
- `QC_Day`: Quality control for daytime LST
- `QC_Night`: Quality control for nighttime LST

**Health Research Applications**:
- Urban heat island health impacts
- Fine-scale temperature exposure assessment
- Heat stress mapping in cities
- Environmental justice studies

**Usage Example**:
```python
# Load MODIS LST data
modis_lst = ee.ImageCollection('MODIS/006/MOD11A1') \
    .filterDate('2020-01-01', '2022-12-31') \
    .filterBounds(study_area)

# Convert from Kelvin to Celsius and apply quality mask
def process_lst(image):
    lst_day = image.select('LST_Day_1km').multiply(0.02).subtract(273.15)
    lst_night = image.select('LST_Night_1km').multiply(0.02).subtract(273.15)
    
    # Apply quality control mask
    qc_day = image.select('QC_Day')
    qc_night = image.select('QC_Night')
    
    # Mask poor quality pixels
    good_quality = qc_day.bitwiseAnd(3).eq(0)  # Good quality flag
    
    return lst_day.updateMask(good_quality) \
        .addBands(lst_night.updateMask(good_quality)) \
        .rename(['LST_Day_C', 'LST_Night_C']) \
        .copyProperties(image, ['system:time_start'])

lst_processed = modis_lst.map(process_lst)
```

**Quality and Limitations**:
- ✅ High spatial resolution (1 km)
- ✅ Direct satellite observations
- ✅ Separate day/night measurements
- ⚠️ Cloud cover can cause data gaps
- ⚠️ Land surface temperature ≠ air temperature
- ⚠️ Quality varies by season and location

---

### 3. CHIRPS Precipitation Data

**Dataset ID**: `UCSB-CHG/CHIRPS/DAILY`

**Overview**: Climate Hazards Group InfraRed Precipitation with Station data (CHIRPS) provides high-resolution precipitation estimates, particularly valuable for tropical and subtropical regions.

**Key Specifications**:
- **Temporal Coverage**: 1981-01-01 to near present
- **Spatial Resolution**: 0.05° (~5.5 km)
- **Temporal Resolution**: Daily
- **Update Frequency**: Regular updates
- **Data Provider**: UC Santa Barbara Climate Hazards Group

**Available Variables**:
- `precipitation`: Daily precipitation estimate (mm)

**Health Research Applications**:
- Vector-borne disease modeling (malaria, dengue)
- Water-related disease analysis
- Flooding and health impact studies
- Seasonal disease pattern analysis

**Usage Example**:
```python
# Load CHIRPS precipitation data
chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
    .filterDate('2020-01-01', '2022-12-31') \
    .filterBounds(study_area)

# Calculate monthly precipitation totals
def monthly_precip(year, month):
    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')
    
    monthly_sum = chirps.filterDate(start_date, end_date) \
        .select('precipitation') \
        .sum() \
        .set('year', year) \
        .set('month', month) \
        .set('system:time_start', start_date.millis())
    
    return monthly_sum

# Create monthly precipitation collection
years = ee.List.sequence(2020, 2022)
months = ee.List.sequence(1, 12)
monthly_precip_collection = ee.ImageCollection.fromImages(
    years.map(lambda y: months.map(lambda m: monthly_precip(y, m))).flatten()
)
```

**Quality and Limitations**:
- ✅ High spatial resolution
- ✅ Good performance in tropical regions
- ✅ Long temporal record
- ⚠️ Lower accuracy in mountainous areas
- ⚠️ Estimates, not direct measurements
- ⚠️ Some regional biases

---

### 4. TerraClimate

**Dataset ID**: `IDAHO_EPSCOR/TERRACLIMATE`

**Overview**: TerraClimate provides monthly climate and water balance data with global coverage, useful for broader climate-health analyses.

**Key Specifications**:
- **Temporal Coverage**: 1958-01-01 to present
- **Spatial Resolution**: 1/24° (~4 km)
- **Temporal Resolution**: Monthly
- **Update Frequency**: Annual updates
- **Data Provider**: University of Idaho

**Available Variables**:
- `tmmx`: Maximum temperature (°C)
- `tmmn`: Minimum temperature (°C)
- `ppt`: Precipitation accumulation (mm)
- `vs`: Wind speed (m/s)
- `vpd`: Vapor pressure deficit (kPa)
- `pet`: Potential evapotranspiration (mm)

**Health Research Applications**:
- Long-term climate-health trend analysis
- Water balance and health relationships
- Drought impact on health
- Climate change health projections

---

## Data Selection Guidelines

### For Temperature-Health Studies:
1. **Daily analysis**: ERA5-Land Daily Aggregated
2. **Urban studies**: MODIS LST for high spatial resolution
3. **Long-term trends**: TerraClimate for 60+ year records
4. **Air temperature**: ERA5-Land (not MODIS LST)

### For Precipitation-Health Studies:
1. **Tropical/subtropical regions**: CHIRPS
2. **Global analysis**: ERA5-Land precipitation
3. **Monthly analysis**: TerraClimate
4. **Drought studies**: TerraClimate (includes drought indices)

### For Vector-Borne Disease Studies:
1. **Temperature**: ERA5-Land daily temperature
2. **Precipitation**: CHIRPS daily precipitation
3. **Humidity**: ERA5-Land (relative humidity, vapor pressure)
4. **Combined**: TerraClimate for integrated climate variables

## Data Quality Considerations

### Validation
- Compare with local weather station data when available
- Check for outliers and missing data patterns
- Validate using independent datasets
- Document data quality issues in your analysis

### Temporal Consistency
- ERA5-Land: Consistent methodology throughout record
- MODIS: Some sensor degradation over time
- CHIRPS: Algorithm improvements may cause temporal inconsistencies
- TerraClimate: Based on multiple changing input sources

### Spatial Representation
- Consider local topography and land use
- Urban areas may not be well represented in coarse-resolution data
- Coastal areas may have boundary effects
- Mountains can cause significant local variation

## Citation and Attribution

### ERA5-Land
```
Muñoz Sabater, J., (2019): ERA5-Land hourly data from 1981 to present. 
Copernicus Climate Change Service (C3S) Climate Data Store (CDS). 
DOI: 10.24381/cds.e2161bac
```

### MODIS LST
```
Wan, Z., Hook, S., Hulley, G. (2015). MOD11A1 MODIS/Terra Land Surface 
Temperature/Emissivity Daily L3 Global 1km SIN Grid V006. NASA EOSDIS 
Land Processes DAAC. DOI: 10.5067/MODIS/MOD11A1.006
```

### CHIRPS
```
Funk, C., Peterson, P., Landsfeld, M., Pedreros, D., Verdin, J., Shukla, S., 
... & Michaelsen, J. (2015). The climate hazards infrared precipitation 
with stations—a new environmental record for monitoring extremes. 
Scientific data, 2(1), 1-21.
```

### TerraClimate
```
Abatzoglou, J. T., Dobrowski, S. Z., Parks, S. A., & Hegewisch, K. C. (2018). 
TerraClimate, a high-resolution global dataset of monthly climate and 
climatic water balance from 1958–2015. Scientific data, 5(1), 1-12.
```

## Additional Resources

### Documentation
- [Google Earth Engine Data Catalog](https://developers.google.com/earth-engine/datasets)
- [ERA5-Land Documentation](https://confluence.ecmwf.int/display/CKB/ERA5-Land)
- [MODIS LST User Guide](https://lpdaac.usgs.gov/documents/118/MOD11_User_Guide_V6.pdf)

### Validation Tools
- [Climate Data Online (NOAA)](https://www.ncdc.noaa.gov/cdo-web/)
- [Global Summary of the Month](https://www.ncei.noaa.gov/data/gsom/)
- [World Weather Records](https://www.weather.gov.hk/en/wxinfo/climat/world/world.htm)

### Research Examples
- Heat-health relationships using ERA5-Land
- Urban heat island health impacts with MODIS LST
- Malaria-climate relationships using CHIRPS and ERA5-Land
- Long-term climate-health trends with TerraClimate
