# 🚀 Quick Start - Get Results in 5 Minutes!

## Run the Working MVP RIGHT NOW

```bash
# 1. Navigate to your Climate_API directory
cd ~/Documents/Climate_API

# 2. Install the package (if not already done)
pip install -e .

# 3. Install scipy (for statistical analysis)
pip install scipy seaborn

# 4. Run the MVP!
python examples/mvp/johannesburg_heat_health_mvp.py
```

That's it! You'll get:
- ✅ Climate data for Johannesburg 2023
- ✅ Health outcome analysis
- ✅ Statistical correlations
- ✅ Publication-ready figures
- ✅ Research report

## 📂 Outputs

Check the `examples/mvp/mvp_outputs/` directory for:

```
mvp_outputs/
├── exposure_response_curve.png          # Figure for publication
├── time_series_analysis.png             # Temperature & health over time
├── distributed_lag_effects.png          # Lag analysis visualization
├── publication_table.csv                # Table 1 for manuscript
├── heat_threshold_analysis.csv          # Threshold analysis results
├── distributed_lag_results.csv          # Detailed lag results
├── merged_climate_health_data.csv       # Full dataset
└── preterm_births_analysis.txt          # Research report
```

## 📊 What the MVP Does

1. **Extracts** real temperature data for Johannesburg
2. **Generates** realistic health outcome data (you'll replace with real data)
3. **Merges** climate and health data with temporal lags
4. **Analyzes**:
   - Correlations
   - Heat thresholds (25°C, 28°C, 30°C, 32°C, 35°C)
   - Distributed lag effects (0-30 days)
   - Relative risks
5. **Produces** publication-ready outputs

## 🔄 Next Steps: Use Your Real Data

Replace the synthetic health data with your actual hospital/clinic data:

```python
# Instead of generating synthetic data...
# health_df = generate_realistic_health_data(climate_df)

# Load your actual data
health_df = pd.read_csv('your_hospital_data.csv')

# Make sure it has these columns:
# - date: datetime
# - preterm_births: count
# - total_births: count
# - preterm_rate: rate per 1000 (or will be calculated)
```

## 🏥 Your Research Questions

**"Does heat increase preterm birth risk in Johannesburg?"**
→ Run the MVP, check correlation and threshold analysis

**"What's the lag between heat exposure and outcomes?"**
→ Check the distributed lag results

**"Which temperature threshold is critical?"**
→ Check the heat threshold analysis

**"How do I make publication figures?"**
→ The MVP already created them!

## 📧 If You Get Errors

### Google Earth Engine Authentication Error?
```bash
# Authenticate with GEE
earthengine authenticate

# Set your project ID in the script
# Edit line 65 in johannesburg_heat_health_mvp.py:
# project_id="your-gee-project-id"
```

### Missing Dependencies?
```bash
pip install scipy seaborn matplotlib pandas numpy
```

### No GEE Access?
The MVP automatically creates sample data if GEE fails!

## 🎉 Success!

If you see this output, it worked:
```
✅ MVP ANALYSIS COMPLETE!
📊 Key Findings:
  • Correlation: r = 0.XXX
  • Strongest heat threshold: XX°C
  • Max relative risk: X.XX
```

## 💡 What Makes This Special?

✅ **Working Example**: Not just documentation - actual running code
✅ **Your Data**: Johannesburg-specific
✅ **Your Research**: Heat-health focus
✅ **Publication Ready**: Figures and tables done
✅ **5 Minutes**: Results immediately

---

**Now go run it!** 🚀

```bash
python examples/mvp/johannesburg_heat_health_mvp.py
```
