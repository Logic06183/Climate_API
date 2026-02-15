# 🏥 Climate-Health Research Optimization Guide

## How This Platform is Optimized for YOUR Research

Based on your Heat Centre work, pregnancy outcomes, and climate-health research needs.

---

## 🎯 Specific Optimizations for Your Use Cases

### 1. **Temporal Lag Analysis** ⏰

**Your Need**: Heat exposure affects pregnancy outcomes days to weeks later.

**Optimization**:
```python
# Automatically creates lagged exposure variables
merged = integrator.merge_climate_health(
    climate_df, health_df,
    lag_days=[0, 7, 14, 21, 30]  # Test multiple exposure windows
)
```

**Research Application**:
- Preterm births: Test 0-30 day lags
- Cardiovascular events: 0-7 day lags
- Heat stress in pregnancy: Cumulative exposure over weeks

---

### 2. **Heat Threshold Analysis** 🌡️

**Your Need**: Identify critical temperature thresholds for interventions.

**Optimization**:
```python
# Automatically tests multiple thresholds
threshold_results = integrator.analyze_heat_thresholds(
    merged_df,
    temperature_col='tmax_celsius',
    health_outcome_col='preterm_rate',
    thresholds=[25, 28, 30, 32, 35]  # Johannesburg-relevant
)
```

**Research Application**:
- Define heat wave thresholds
- Identify vulnerable populations
- Guide public health warnings
- Policy recommendations

---

### 3. **Publication-Ready Outputs** 📊

**Your Need**: Tables and figures for peer-reviewed publications.

**Optimization**:
```python
# Automatically generates publication tables
pub_table = integrator.create_publication_table(threshold_results)

# Creates professional figures
fig = integrator.plot_exposure_response(merged_df, 'temp', 'outcome')
fig.savefig('figure1.png', dpi=300)  # Journal-quality resolution
```

**Output Format**:
```
Threshold (°C) | Days Exposed | Mean Outcome | Relative Risk | P-value | Significance
≥30           | 45           | 9.2          | 1.15         | 0.023   | Yes
≥32           | 23           | 10.1         | 1.26         | 0.001   | Yes
```

---

### 4. **Data Quality Validation** ✅

**Your Need**: Research integrity and reproducibility.

**Optimization**:
```python
# Automatic quality checks before analysis
validator = DataQualityValidator()
report = validator.validate_climate_data(data)

# Catches:
# - Missing data gaps
# - Outliers
# - Duplicate dates
# - Incomplete periods
```

**Research Benefit**:
- Prevents publication of flawed analyses
- Ensures reproducibility
- Documents data provenance

---

### 5. **Distributed Lag Models** 📈

**Your Need**: Understand how exposure effects vary over time.

**Optimization**:
```python
# Calculates effect at each lag period
lag_results = integrator.calculate_distributed_lag(
    merged_df,
    exposure_col='tmax_celsius',
    outcome_col='preterm_rate',
    max_lag=30
)
```

**Research Application**:
- Identify critical exposure windows
- Understand biological mechanisms
- Guide intervention timing

---

### 6. **Intelligent Caching** 💾

**Your Need**: Avoid re-downloading data (GEE quota limits).

**Optimization**:
```python
# Automatically caches extracted data
@cached(max_age_hours=24)
def extract_climate_data(...):
    # Results cached for 24 hours
    # Re-run analysis without re-downloading
```

**Research Benefit**:
- Iterate on analysis quickly
- Respect API quotas
- Share cached data with collaborators

---

### 7. **Exposure-Response Curves** 📉

**Your Need**: Show non-linear relationships for publications.

**Optimization**:
```python
# Creates binned exposure-response curves
fig = integrator.plot_exposure_response(
    merged_df,
    exposure_col='tmax_celsius',
    outcome_col='preterm_rate',
    bins=20
)
```

**Research Application**:
- Visualize dose-response
- Identify non-linear effects
- Publication Figure 1

---

## 🔬 Research Workflow Examples

### Example 1: Heat and Preterm Births

```python
# Your complete workflow in 10 lines!
extractor = ClimateDataExtractor()
integrator = ClimateHealthIntegrator()

# Extract heat exposure data
climate = extractor.extract_climate_data(
    lat=-26.2041, lon=28.0473,
    start_date='2020-01-01', end_date='2023-12-31',
    location_name='Johannesburg'
)

# Merge with birth outcomes (your hospital data)
merged = integrator.merge_climate_health(
    climate['daily'], your_birth_data,
    lag_days=[0, 7, 14, 21, 30]
)

# Generate complete research report
report = integrator.generate_research_report(
    merged, 'tmax_celsius', 'preterm_rate',
    output_path='./manuscript/analysis_report.txt'
)

# Done! Publication tables and figures ready.
```

---

### Example 2: Heat Vulnerability Index (HVI)

```python
from climate_toolkit.analysis import ImageExplorer
from climate_toolkit.workflows import HVICalculator

# Load satellite imagery
explorer = ImageExplorer()
explorer.load_image('johannesburg_landsat.tif')

# Calculate HVI
hvi_calc = HVICalculator()
hvi_result = hvi_calc.calculate_hvi(
    temperature_band=explorer.image[5],  # Thermal band
    ndvi_band=explorer.image[4],  # Vegetation
)

# Export risk maps
hvi_calc.export_risk_map(hvi_result, 'joburg_hvi.tif')
```

---

### Example 3: Multi-City Comparison

```python
cities = [
    {'name': 'Johannesburg', 'lat': -26.2041, 'lon': 28.0473},
    {'name': 'Cape Town', 'lat': -33.9249, 'lon': 18.4241},
    {'name': 'Durban', 'lat': -29.8587, 'lon': 31.0218},
]

results = []
for city in cities:
    climate = extractor.extract_climate_data(**city, ...)
    merged = integrator.merge_climate_health(climate, health_data[city['name']])
    report = integrator.generate_research_report(merged, ...)
    results.append(report)

# Compare heat effects across cities
comparison_table = compare_cities(results)
```

---

## 📊 Publication Workflow

### Step 1: Extract Climate Data
```bash
climate-extract extract \
    --lat -26.2041 --lon 28.0473 \
    --start-date 2020-01-01 --end-date 2023-12-31 \
    --location "Johannesburg" \
    --output-dir ./data
```

### Step 2: Prepare Health Data
```python
# Your hospital data
health_df = pd.read_csv('hospital_births.csv')

# Must have 'date' column and outcome variables
# Example columns: date, total_births, preterm_births, gestational_age
```

### Step 3: Run Analysis
```python
python examples/mvp/johannesburg_heat_health_mvp.py
```

### Step 4: Get Publication Outputs
```
mvp_outputs/
├── exposure_response_curve.png      # Figure 1
├── time_series_analysis.png         # Figure 2
├── distributed_lag_effects.png      # Figure 3
├── publication_table.csv            # Table 1
├── heat_threshold_analysis.csv      # Table 2
├── preterm_births_analysis.txt      # Methods text
└── merged_climate_health_data.csv   # Supplementary data
```

---

## 🎓 Research Best Practices Built-In

### 1. **Confounding Control**
```python
# Add confounders to your analysis
merged['air_pollution'] = pollution_data
merged['humidity'] = humidity_data

# Model controls for confounding
from sklearn.linear_model import LinearRegression

model = LinearRegression()
X = merged[['tmax_celsius', 'air_pollution', 'humidity']]
y = merged['preterm_rate']
model.fit(X, y)
```

### 2. **Stratified Analysis**
```python
# Analyze by subgroups
for age_group in ['<20', '20-35', '>35']:
    subset = merged[merged['maternal_age_group'] == age_group]
    report = integrator.generate_research_report(subset, ...)
```

### 3. **Sensitivity Analysis**
```python
# Test different lag specifications
for max_lag in [14, 21, 30, 60]:
    lag_results = integrator.calculate_distributed_lag(
        merged, 'temp', 'outcome', max_lag=max_lag
    )
```

---

## 🚀 Next-Level Features

### 1. **Batch Processing**
```python
# Process multiple years automatically
for year in range(2015, 2024):
    climate = extractor.extract_climate_data(
        start_date=f'{year}-01-01',
        end_date=f'{year}-12-31',
        ...
    )
    # Analysis runs automatically with caching
```

### 2. **Custom Health Metrics**
```python
# Define your own health metrics
class CustomHealthAnalyzer(ClimateHealthIntegrator):
    def calculate_heat_stress_index(self, merged_df):
        # Your custom metric
        hsi = (merged_df['tmax_celsius'] > 32).sum() / len(merged_df)
        return hsi
```

### 3. **Integration with R**
```python
# Export for R analysis
merged.to_csv('for_r_analysis.csv')

# Or use rpy2 for seamless integration
from rpy2.robjects import pandas2ri
pandas2ri.activate()
```

---

## 📝 Methods Section Template

Here's what to include in your manuscript methods:

```
Climate Data Extraction:
Daily temperature data for Johannesburg (26.2°S, 28.0°E) were extracted
from the ERA5-Land reanalysis dataset using the Climate Toolkit package
(v0.2.0) via the Google Earth Engine API. Temperature data were quality-
checked for missing values, outliers, and temporal gaps using automated
validation procedures.

Exposure Assessment:
Heat exposure was defined using daily maximum temperature. We examined
lagged effects at 0, 7, 14, 21, and 30 days prior to health outcomes to
capture potential delayed effects of heat exposure on pregnancy outcomes.

Statistical Analysis:
We calculated Pearson correlation coefficients between temperature and
health outcomes. Heat threshold analysis examined outcomes at temperature
cutpoints of 25, 28, 30, 32, and 35°C. Distributed lag models were fit
to identify critical exposure windows. All analyses were conducted in
Python 3.11 using the Climate Toolkit package.
```

---

## 🏆 Why This is Optimized for YOU

✅ **Epidemiological Focus**: Designed for health outcome research
✅ **Lag Analysis**: Built-in temporal lag handling
✅ **Publication Ready**: Professional outputs
✅ **Quality Control**: Automatic data validation
✅ **Reproducible**: Config files, caching, version control
✅ **Fast**: Intelligent caching saves time
✅ **Tested**: 40+ tests ensure reliability
✅ **Documented**: Clear examples for your use cases

---

## 🎯 Your Specific Research Questions

### "Does heat increase preterm birth risk?"
→ Use `merge_climate_health()` + `analyze_heat_thresholds()`

### "What's the critical exposure window?"
→ Use `calculate_distributed_lag()`

### "Which neighborhoods are most vulnerable?"
→ Use spatial HVI analysis (coming next)

### "How do I communicate findings to policymakers?"
→ Use `create_publication_table()` + professional visualizations

---

## 📞 Support for Your Research

**Common Questions**:
1. **"How do I add my hospital data?"** → See Example 1 above
2. **"What lag periods should I test?"** → Start with [0, 7, 14, 21, 30]
3. **"How do I control for confounding?"** → See Best Practices section
4. **"Can I use this for my dissertation?"** → Yes! MIT licensed

**Citation** (when you publish):
```
Climate data were processed using the Climate-Health Intelligence Platform
(Climate Toolkit v0.2.0), an open-source Python package for climate-health
research (github.com/your-repo).
```

---

*Built specifically for climate-health researchers who need reliable,
publication-ready analysis with minimal coding.*
