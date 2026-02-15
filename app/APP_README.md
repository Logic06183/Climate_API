# 🏥 Climate-Health Analysis Web App

## Launch the App

### Option 1: Double-click
```
Double-click RUN_APP.sh
```

### Option 2: Terminal
```bash
cd ~/Documents/Climate_API/app
./RUN_APP.sh
```

### Option 3: Direct command
```bash
cd ~/Documents/Climate_API/app
streamlit run climate_health_app.py
```

The app will open in your browser at: **http://localhost:8501**

---

## 📋 How to Use

### Step 1: Prepare Your Health Data

Create a CSV file with:
- **`date`** column (YYYY-MM-DD) - **REQUIRED**
- Health outcome columns (e.g., `preterm_births`, `cvd_events`)

Example:
```csv
date,total_births,preterm_births,cvd_events
2023-01-01,150,12,25
2023-01-02,148,11,23
2023-01-03,152,13,27
```

Download the template from the app (Tab 1).

### Step 2: Upload Data (Tab 1)
1. Click "Upload Data" tab
2. Download template if needed
3. Upload your CSV file
4. App validates your data automatically

### Step 3: Extract Climate (Tab 2)
1. Configure location (sidebar)
2. Set date range (sidebar)
3. Click "Extract Climate Data"
4. Wait ~30 seconds for GEE extraction

### Step 4: Run Analysis (Tab 3)
1. Select health outcome variable
2. Click "Run Analysis"
3. View results:
   - Correlation statistics
   - Heat threshold analysis
   - Exposure-response curves
   - Distributed lag effects
4. Download publication tables

### Step 5: Maps (Tab 4)
- View study location
- Interactive maps (coming soon)

---

## ⚙️ Configuration (Sidebar)

### Google Earth Engine
- Enter your GEE project ID
- Get one at: https://earthengine.google.com

### Study Location
- Location name (for labels)
- Latitude and longitude
- Defaults to Johannesburg

### Study Period
- Start and end dates
- Determines climate data extraction period

### Analysis Options
- **Lag Periods**: Test different exposure windows (e.g., 0,7,14,21,30 days)
- **Heat Thresholds**: Temperature cutpoints (e.g., 25,28,30,32,35°C)

---

## 📊 Features

### ✅ No Synthetic Data
- Only uses your real uploaded health data
- No fake or generated data

### ✅ Automatic Climate Extraction
- Pulls real temperature data from Google Earth Engine
- Handles chunked downloads automatically

### ✅ Statistical Analysis
- Pearson correlations
- Heat threshold analysis
- Distributed lag models
- Relative risk calculations

### ✅ Publication Ready
- Professional figures
- Formatted tables
- Downloadable results

### ✅ Data Validation
- Automatic format checking
- Missing value detection
- Date validation
- Helpful error messages

---

## 💾 Downloads Available

From the app, you can download:

1. **Template CSV** - Example data format
2. **Climate Data** - Extracted temperature data
3. **Merged Dataset** - Climate + health combined
4. **Threshold Analysis** - Heat threshold results
5. **Lag Analysis** - Distributed lag results

---

## 🔧 Troubleshooting

### App won't start?
```bash
pip install streamlit
```

### GEE authentication error?
```bash
earthengine authenticate
```

### Can't upload file?
- Check file is CSV format
- Ensure 'date' column exists
- Use YYYY-MM-DD date format

### Analysis fails?
- Check health and climate data both loaded
- Verify date ranges overlap
- Check for sufficient data points

---

## 🎓 Example Workflows

### Preterm Births & Heat
1. Upload birth registry data
2. Extract temperature for hospital location
3. Analyze with 0-30 day lags
4. Identify critical heat thresholds

### Cardiovascular Events
1. Upload daily CVD event counts
2. Extract temperature data
3. Use shorter lags (0-7 days)
4. Test heat wave thresholds

### Multi-City Comparison
1. Run app for each city separately
2. Compare results across cities
3. Download tables for meta-analysis

---

## 📱 Sharing with Collaborators

Share this app with other researchers:

```bash
# They just need to:
1. Clone/copy the Climate_API folder
2. cd Climate_API/app
3. ./RUN_APP.sh
```

Or use Streamlit Cloud for web hosting (free):
https://streamlit.io/cloud

---

## 🚀 Next Steps

After analyzing in the app:

1. **Export Results**
   - Download all CSVs
   - Save figures (right-click)

2. **Create Manuscript**
   - Use threshold analysis for Table 1
   - Use exposure-response curve for Figure 1
   - Use lag analysis for Figure 2

3. **Extended Analysis**
   - Import downloaded CSVs into R/Stata
   - Add confounders
   - Run stratified analysis

---

## 💡 Tips

- **Start small**: Test with 1 month of data first
- **Check dates**: Ensure health and climate dates overlap
- **Try different lags**: Health effects may lag exposure by days/weeks
- **Save results**: Download CSVs after each analysis
- **Document settings**: Note what parameters worked best

---

**You now have a web app that researchers can actually use!** 🎉

No coding required - just upload data and click buttons!
