# Quick Start Guide

## Local Testing (Fastest Way)

```bash
# Navigate to webapp directory
cd webapp

# Run the start script
./start.sh
```

Then open your browser to: **http://localhost:8000**

## What You'll See

### Single Location Tab
1. **Interactive Map** - Click anywhere in South Africa to select location
2. **Preset Locations** - Quick buttons for Soweto, Johannesburg, Cape Town, etc.
3. **Date Selection** - Pick your study period
4. **Extract Button** - Click to start extraction
5. **Results** - View charts and download data

### Batch CSV Tab
1. **Upload CSV** - Upload file with multiple locations
2. **Date Range** - Same date range applies to all locations
3. **Process Button** - Extract data for all locations
4. **Download** - Get Excel file with all results

## Sample Workflow

### Single Location Extraction
1. Click "Soweto, Johannesburg" preset button
2. Set date range (defaults to last year)
3. Click "🚀 Extract Climate Data"
4. View temperature chart
5. Download JSON data

### Batch CSV Processing
1. Click "Download Sample CSV" to get template
2. Edit CSV with your locations
3. Upload the file
4. Set date range
5. Click "🚀 Process All Locations"
6. Download Excel file with all results

## CSV Format Example

```csv
location_name,latitude,longitude
Clinic A,-26.2678,27.8607
Clinic B,-26.2041,28.0473
Clinic C,-33.9249,18.4241
```

## Cloud Deployment

```bash
# From webapp directory
gcloud run deploy climate-health-app \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --project joburg-hvi
```

After deployment, you'll get a URL like:
```
https://climate-health-app-xxxxx-uc.a.run.app
```

Share this URL with your team - they can access the tool from any browser!

## Troubleshooting

**Earth Engine auth error?**
```bash
earthengine authenticate --force
```

**Module not found?**
```bash
cd webapp/backend
pip install -r requirements.txt
```

**Can't access localhost:8000?**
- Check if port 8000 is already in use
- Try: `lsof -ti:8000 | xargs kill` to free the port

## Features at a Glance

✅ Interactive map for point-and-click location selection
✅ Preset locations for major South African cities
✅ CSV upload for batch processing multiple locations
✅ Real-time progress indicators
✅ Temperature visualization charts
✅ Multiple export formats (JSON, Excel)
✅ Responsive design works on desktop and tablet
✅ Ready for Cloud Run deployment

## Next Steps

1. **Test Locally**: Run `./start.sh` and try the interface
2. **Prepare CSV**: Create a CSV with your study locations
3. **Deploy**: Deploy to Cloud Run when ready
4. **Share**: Give the URL to your research team

---

Need help? Check the full README.md for detailed documentation.
