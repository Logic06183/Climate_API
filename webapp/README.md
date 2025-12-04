# Climate-Health Data Extraction Web Application

A modern web application for extracting climate data from Google Earth Engine for health research. Features an interactive map, batch CSV processing, and real-time progress tracking.

## Features

### 🗺️ Single Location Mode
- **Interactive Map**: Click anywhere to select study location
- **Preset Locations**: Quick access to major South African cities
- **Real-time Progress**: Live updates during data extraction
- **Data Visualization**: Interactive charts showing temperature trends
- **Multiple Export Formats**: Download as JSON

### 📊 Batch CSV Mode
- **Bulk Processing**: Upload CSV with multiple locations
- **Automatic Processing**: Extract data for all locations simultaneously
- **Excel Output**: Combined Excel file with separate sheets per location
- **Summary Statistics**: Overview of all extracted data

## Architecture

- **Backend**: FastAPI (Python 3.11)
  - Google Earth Engine integration
  - RESTful API endpoints
  - WebSocket support for progress updates

- **Frontend**: Modern HTML/JavaScript
  - Tailwind CSS for styling
  - Leaflet for interactive maps
  - Chart.js for data visualization

- **Deployment**: Google Cloud Run
  - Auto-scaling
  - HTTPS enabled
  - Pay-per-use pricing

## Local Development

### Prerequisites
- Python 3.11+
- Google Earth Engine account
- Earth Engine credentials configured

### Setup

1. **Install Dependencies**
   ```bash
   cd webapp/backend
   pip install -r requirements.txt
   ```

2. **Start the Server**
   ```bash
   # From webapp/backend directory
   python main.py
   ```

3. **Access the Application**
   Open your browser to: `http://localhost:8000`

### Testing the API

Test the API endpoints directly:

```bash
# Health check
curl http://localhost:8000/health

# Get preset locations
curl http://localhost:8000/presets

# Extract data for a location
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": -26.2678,
    "longitude": 27.8607,
    "location_name": "Soweto",
    "start_date": "2023-01-01",
    "end_date": "2023-01-31",
    "buffer_km": 10
  }'
```

## Cloud Deployment (Google Cloud Run)

### Prerequisites
- Google Cloud account with billing enabled
- `joburg-hvi` project (or your own project)
- Google Cloud SDK installed
- Earth Engine API enabled

### Step 1: Prepare Credentials

The application needs Google Earth Engine credentials. You have two options:

**Option A: Use Application Default Credentials (Recommended)**
```bash
gcloud auth application-default login
```

**Option B: Service Account**
1. Create a service account in Google Cloud Console
2. Register it with Earth Engine
3. Download the service account key JSON
4. Mount it as a secret in Cloud Run

### Step 2: Build and Deploy

```bash
# Navigate to webapp directory
cd webapp

# Set your project ID
export PROJECT_ID=joburg-hvi

# Build the container
gcloud builds submit --tag gcr.io/${PROJECT_ID}/climate-health-app

# Deploy to Cloud Run
gcloud run deploy climate-health-app \
  --image gcr.io/${PROJECT_ID}/climate-health-app \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 600 \
  --set-env-vars "PROJECT_ID=${PROJECT_ID}"
```

### Step 3: Access Your Application

After deployment, you'll receive a URL like:
```
https://climate-health-app-xxxxx-uc.a.run.app
```

Open this URL in your browser to access the application!

### Alternative: One-Command Deployment

```bash
# From the webapp directory
gcloud run deploy climate-health-app \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --project joburg-hvi
```

## CSV Format for Batch Processing

Your CSV file should have these columns:

| Column | Description | Required |
|--------|-------------|----------|
| `location_name` | Name of the location | Yes |
| `latitude` or `lat` | Latitude coordinate (-90 to 90) | Yes |
| `longitude` or `lon` | Longitude coordinate (-180 to 180) | Yes |

### Example CSV

```csv
location_name,latitude,longitude
Soweto Clinic,-26.2678,27.8607
Johannesburg Hospital,-26.2041,28.0473
Cape Town Clinic,-33.9249,18.4241
Durban Hospital,-29.8587,31.0218
Pretoria Medical Center,-25.7479,28.2293
```

### Download Sample

Click "Download Sample CSV" in the Batch Upload tab to get a template.

## API Endpoints

### GET /presets
Get list of preset locations

**Response:**
```json
[
  {
    "name": "Soweto, Johannesburg",
    "latitude": -26.2678,
    "longitude": 27.8607,
    "description": "Major township in Johannesburg"
  }
]
```

### POST /extract
Extract climate data for a single location

**Request Body:**
```json
{
  "latitude": -26.2678,
  "longitude": 27.8607,
  "location_name": "Soweto",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "buffer_km": 10
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully extracted 365 records",
  "location": "Soweto",
  "records_extracted": 365,
  "temperature_range": {
    "min": 12.5,
    "max": 28.3,
    "mean": 19.8
  },
  "data": {
    "daily": [...]
  }
}
```

### POST /extract/batch
Extract climate data for multiple locations from CSV

**Form Data:**
- `file`: CSV file with locations
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)
- `buffer_km`: Buffer radius in kilometers

**Response:**
Excel file with multiple sheets (one per location + summary)

### GET /health
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "gee_initialized": true,
  "timestamp": "2024-01-01T12:00:00"
}
```

## Troubleshooting

### Earth Engine Authentication Issues

If you get authentication errors:

1. **Local Development:**
   ```bash
   earthengine authenticate --force
   ```

2. **Cloud Run:**
   - Ensure your service account is registered with Earth Engine
   - Or use Application Default Credentials

### CORS Issues

If you're accessing the API from a different domain:
- Update `allow_origins` in `backend/main.py`
- Or deploy frontend and backend together (current setup)

### Memory Issues

If processing fails for large date ranges:
- Increase Cloud Run memory: `--memory 4Gi`
- Reduce date range or buffer size
- Process in smaller batches

### Rate Limits

Google Earth Engine has rate limits:
- Reduce concurrent requests
- Add delays between batch processing
- Use smaller buffer sizes

## Cost Estimation

### Cloud Run Pricing (approximate)
- **Free tier**: 2 million requests/month, 360,000 GB-seconds/month
- **Beyond free tier**: ~$0.00002400 per request
- **Typical extraction**: $0.001 - $0.01 per location

### Example Monthly Costs
- 100 extractions/month: **FREE**
- 1,000 extractions/month: ~$10
- 10,000 extractions/month: ~$100

*Actual costs depend on data volume and processing time*

## Security Considerations

### For Production Use

1. **Authentication**: Add user authentication
2. **Rate Limiting**: Implement request rate limiting
3. **CORS**: Restrict origins to your domain
4. **API Keys**: Add API key requirement
5. **Input Validation**: Enhanced validation on all inputs

### Example Authentication (modify main.py)

```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/extract")
async def extract_single_location(
    request: LocationRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Verify credentials
    # ... rest of function
```

## Support

For issues or questions:
- Check the main repository README
- Review the troubleshooting section
- Contact the development team

## License

MIT License - See main repository LICENSE file

---

**Built for health researchers by the Heat Centre**
*Enabling accessible climate-health research worldwide*
