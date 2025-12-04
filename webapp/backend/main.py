"""
Climate-Health Data Extraction API
FastAPI backend for extracting climate data from Google Earth Engine
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List
import pandas as pd
import json
import os
import sys
from datetime import datetime
import asyncio
from io import BytesIO
import traceback

# Add parent directory to path to import climate utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src.climate_utils import ClimateDataExtractor

app = FastAPI(
    title="Climate-Health Data API",
    description="Extract climate data for health research from Google Earth Engine",
    version="1.0.0"
)

# Mount static files (frontend)
frontend_path = os.path.join(os.path.dirname(__file__), '../frontend')
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize climate data extractor with project ID
PROJECT_ID = os.getenv('PROJECT_ID', 'joburg-hvi')
extractor = ClimateDataExtractor(project_id=PROJECT_ID)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class LocationRequest(BaseModel):
    """Request model for single location extraction"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude (-90 to 90)")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude (-180 to 180)")
    location_name: str = Field(..., min_length=1, description="Name of the location")
    start_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$', description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$', description="End date (YYYY-MM-DD)")
    buffer_km: float = Field(default=10, ge=1, le=100, description="Buffer radius in kilometers")
    variables: Optional[List[str]] = Field(default=None, description="List of climate variables to extract. Options: temperature, precipitation, humidity, wind, solar, pressure, evapotranspiration")

class ExtractionResponse(BaseModel):
    """Response model for extraction results"""
    status: str
    message: str
    location: str
    records_extracted: int
    temperature_range: Optional[dict] = None
    data: Optional[dict] = None
    download_url: Optional[str] = None

class PresetLocation(BaseModel):
    """Preset location model"""
    name: str
    latitude: float
    longitude: float
    description: str

# ============================================================================
# PRESET LOCATIONS
# ============================================================================

PRESET_LOCATIONS = [
    PresetLocation(
        name="Soweto, Johannesburg",
        latitude=-26.2678,
        longitude=27.8607,
        description="Major township in Johannesburg - Case study location"
    ),
    PresetLocation(
        name="Johannesburg CBD",
        latitude=-26.2041,
        longitude=28.0473,
        description="Johannesburg Central Business District"
    ),
    PresetLocation(
        name="Cape Town",
        latitude=-33.9249,
        longitude=18.4241,
        description="Cape Town metropolitan area"
    ),
    PresetLocation(
        name="Durban",
        latitude=-29.8587,
        longitude=31.0218,
        description="Durban metropolitan area"
    ),
    PresetLocation(
        name="Pretoria",
        latitude=-25.7479,
        longitude=28.2293,
        description="Pretoria/Tshwane metropolitan area"
    ),
]

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend application"""
    frontend_file = os.path.join(os.path.dirname(__file__), '../frontend/index.html')
    if os.path.exists(frontend_file):
        with open(frontend_file, 'r') as f:
            return f.read()
    return {
        "name": "Climate-Health Data Extraction API",
        "version": "1.0.0",
        "description": "Extract climate data for health research",
        "endpoints": {
            "GET /presets": "Get preset locations",
            "POST /extract": "Extract data for single location",
            "POST /extract/batch": "Extract data for multiple locations from CSV",
            "GET /health": "Health check endpoint"
        }
    }

@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "name": "Climate-Health Data Extraction API",
        "version": "1.0.0",
        "description": "Extract climate data for health research",
        "endpoints": {
            "GET /presets": "Get preset locations",
            "POST /extract": "Extract data for single location",
            "POST /extract/batch": "Extract data for multiple locations from CSV",
            "GET /health": "Health check endpoint"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "gee_initialized": extractor.initialized,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/presets", response_model=List[PresetLocation])
async def get_presets():
    """Get list of preset locations"""
    return PRESET_LOCATIONS

@app.get("/geocode")
async def geocode_location(query: str):
    """
    Geocode a location name to coordinates
    Uses Nominatim (OpenStreetMap) - free, no API key required
    """
    try:
        import requests

        # Use Nominatim (OpenStreetMap) geocoding - free, no API key needed
        url = f"https://nominatim.openstreetmap.org/search"
        params = {
            'q': query,
            'format': 'json',
            'limit': 5,
            'countrycodes': 'za',
            'addressdetails': 1
        }
        headers = {'User-Agent': 'ClimateHealthApp/1.0'}

        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            formatted_results = []
            for item in data:
                formatted_results.append({
                    "name": item.get('name', item.get('display_name', '').split(',')[0]),
                    "display_name": item.get('display_name', ''),
                    "lat": float(item['lat']),
                    "lon": float(item['lon']),
                    "type": item.get('type', 'location')
                })
            return {"results": formatted_results}
        else:
            raise HTTPException(status_code=500, detail="Geocoding service unavailable")

    except Exception as e:
        print(f"Geocoding error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Geocoding failed: {str(e)}")

@app.post("/extract", response_model=ExtractionResponse)
async def extract_single_location(request: LocationRequest):
    """
    Extract climate data for a single location
    """
    try:
        print(f"Extracting data for {request.location_name}")

        # Create study area
        geometry = extractor.create_study_area(
            lat=request.latitude,
            lon=request.longitude,
            buffer_km=request.buffer_km
        )

        # Create point
        point = extractor.create_point(request.latitude, request.longitude)

        # Extract climate data using new multi-variable method
        df = extractor.extract_climate_data(
            geometry=geometry,
            point=point,
            start_date=request.start_date,
            end_date=request.end_date,
            variables=request.variables
        )

        if df.empty:
            raise HTTPException(status_code=404, detail="No data found for specified period")

        # Calculate statistics based on available columns
        stats = {}
        if 'tmean_celsius' in df.columns:
            stats["temperature"] = {
                "min": float(df['tmean_celsius'].min()),
                "max": float(df['tmax_celsius'].max()) if 'tmax_celsius' in df.columns else float(df['tmean_celsius'].max()),
                "mean": float(df['tmean_celsius'].mean())
            }
        if 'precipitation_mm' in df.columns:
            stats["precipitation"] = {
                "total": float(df['precipitation_mm'].sum()),
                "mean": float(df['precipitation_mm'].mean()),
                "max": float(df['precipitation_mm'].max())
            }
        if 'wind_speed_ms' in df.columns:
            stats["wind_speed"] = {
                "mean": float(df['wind_speed_ms'].mean()),
                "max": float(df['wind_speed_ms'].max())
            }

        # Convert to dict for response
        data_dict = df.to_dict(orient='records')

        return ExtractionResponse(
            status="success",
            message=f"Successfully extracted {len(df)} records with {len(df.columns)-1} variables",
            location=request.location_name,
            records_extracted=len(df),
            temperature_range=stats,
            data={"daily": data_dict}
        )

    except Exception as e:
        print(f"Error extracting data: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@app.post("/extract/batch")
async def extract_batch_csv(file: UploadFile = File(...), start_date: str = "", end_date: str = "", buffer_km: float = 10):
    """
    Extract climate data for multiple locations from CSV file

    CSV should have columns: location_name, latitude, longitude
    Or: location_name, lat, lon
    """
    try:
        # Validate dates
        if not start_date or not end_date:
            raise HTTPException(status_code=400, detail="start_date and end_date are required")

        # Read CSV
        contents = await file.read()
        df_locations = pd.read_csv(BytesIO(contents))

        # Validate CSV columns
        required_cols = ['latitude', 'longitude']
        alt_cols = ['lat', 'lon']

        if not all(col in df_locations.columns for col in required_cols):
            if all(col in df_locations.columns for col in alt_cols):
                # Rename columns
                df_locations = df_locations.rename(columns={'lat': 'latitude', 'lon': 'longitude'})
            else:
                raise HTTPException(
                    status_code=400,
                    detail="CSV must have columns: location_name, latitude, longitude (or lat, lon)"
                )

        if 'location_name' not in df_locations.columns:
            # Generate location names
            df_locations['location_name'] = [f"Location_{i+1}" for i in range(len(df_locations))]

        # Process each location
        all_results = {}
        total_locations = len(df_locations)

        for idx, row in df_locations.iterrows():
            location_name = row['location_name']
            lat = row['latitude']
            lon = row['longitude']

            print(f"Processing {idx + 1}/{total_locations}: {location_name}")

            try:
                # Create study area
                geometry = extractor.create_study_area(lat=lat, lon=lon, buffer_km=buffer_km)

                # Get temperature data
                collection = extractor.get_era5_temperature(
                    geometry=geometry,
                    start_date=start_date,
                    end_date=end_date
                )

                # Extract time series
                point = extractor.create_point(lat, lon)
                df_temp = extractor.extract_temperature_timeseries(collection, point)

                if not df_temp.empty:
                    all_results[location_name] = df_temp
                else:
                    print(f"No data found for {location_name}")

            except Exception as e:
                print(f"Error processing {location_name}: {str(e)}")
                continue

        if not all_results:
            raise HTTPException(status_code=404, detail="No data extracted for any location")

        # Create Excel file with multiple sheets
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Summary sheet
            summary_data = []
            for loc_name, df_temp in all_results.items():
                summary_data.append({
                    'Location': loc_name,
                    'Records': len(df_temp),
                    'Mean Temp (°C)': df_temp['tmean_celsius'].mean(),
                    'Max Temp (°C)': df_temp['tmax_celsius'].max(),
                    'Min Temp (°C)': df_temp['tmean_celsius'].min()
                })

            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)

            # Individual location sheets
            for loc_name, df_temp in all_results.items():
                # Sanitize sheet name (Excel limit: 31 chars, no special chars)
                sheet_name = loc_name[:31].replace('/', '_').replace('\\', '_')
                df_temp.to_excel(writer, sheet_name=sheet_name, index=False)

        output.seek(0)

        # Generate filename
        filename = f"climate_data_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in batch extraction: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Batch extraction failed: {str(e)}")

@app.websocket("/ws/extract")
async def websocket_extract(websocket: WebSocket):
    """
    WebSocket endpoint for real-time progress updates during extraction
    """
    await websocket.accept()

    try:
        # Receive extraction parameters
        data = await websocket.receive_json()

        # Send progress updates
        await websocket.send_json({"status": "started", "progress": 0})

        # TODO: Implement actual extraction with progress updates
        # For now, simulate progress
        for i in range(10):
            await asyncio.sleep(0.5)
            await websocket.send_json({
                "status": "processing",
                "progress": (i + 1) * 10,
                "message": f"Processing chunk {i + 1}/10"
            })

        await websocket.send_json({"status": "completed", "progress": 100})

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
