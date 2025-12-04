// Configuration
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : ''; // Same origin when deployed together

// Global variables
let map;
let marker;
let presetLocations = [];
let currentChart = null;

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    initMap();
    await loadPresetLocations();
    setupEventListeners();
    setDefaultDates();
    setupLocationSearch();
});

// ============================================================================
// MAP FUNCTIONALITY
// ============================================================================

function initMap() {
    // Initialize map centered on South Africa
    map = L.map('map').setView([-28.5, 24.5], 6);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    // Add click handler
    map.on('click', onMapClick);
}

function onMapClick(e) {
    const lat = e.latlng.lat.toFixed(4);
    const lon = e.latlng.lng.toFixed(4);

    // Update form fields
    document.getElementById('latitude').value = lat;
    document.getElementById('longitude').value = lon;

    // Update or create marker
    if (marker) {
        marker.setLatLng(e.latlng);
    } else {
        marker = L.marker(e.latlng).addTo(map);
    }

    // Generate location name if empty
    if (!document.getElementById('location-name').value) {
        document.getElementById('location-name').value = `Location (${lat}, ${lon})`;
    }
}

function setMapLocation(lat, lon, name) {
    const latLng = L.latLng(lat, lon);

    // Update form
    document.getElementById('latitude').value = lat;
    document.getElementById('longitude').value = lon;
    document.getElementById('location-name').value = name;

    // Update map
    map.setView(latLng, 10);

    if (marker) {
        marker.setLatLng(latLng);
    } else {
        marker = L.marker(latLng).addTo(map);
    }
}

// ============================================================================
// PRESET LOCATIONS
// ============================================================================

async function loadPresetLocations() {
    try {
        const response = await fetch(`${API_BASE_URL}/presets`);
        presetLocations = await response.json();
        renderPresetButtons();
    } catch (error) {
        console.error('Error loading presets:', error);
    }
}

function renderPresetButtons() {
    const container = document.getElementById('preset-buttons');
    container.innerHTML = '';

    presetLocations.forEach(preset => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'w-full text-left px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200';
        button.innerHTML = `
            <div class="font-medium">${preset.name}</div>
            <div class="text-sm text-gray-600">${preset.description}</div>
        `;
        button.onclick = () => setMapLocation(preset.latitude, preset.longitude, preset.name);
        container.appendChild(button);
    });
}

// ============================================================================
// TAB SWITCHING
// ============================================================================

function switchTab(tab) {
    // Update tab buttons
    document.getElementById('tab-single').classList.remove('tab-active', 'text-blue-600');
    document.getElementById('tab-single').classList.add('text-gray-500', 'border-transparent');
    document.getElementById('tab-batch').classList.remove('tab-active', 'text-blue-600');
    document.getElementById('tab-batch').classList.add('text-gray-500', 'border-transparent');

    // Update content
    document.getElementById('content-single').classList.add('hidden');
    document.getElementById('content-batch').classList.add('hidden');

    if (tab === 'single') {
        document.getElementById('tab-single').classList.add('tab-active', 'text-blue-600');
        document.getElementById('tab-single').classList.remove('text-gray-500', 'border-transparent');
        document.getElementById('content-single').classList.remove('hidden');
    } else {
        document.getElementById('tab-batch').classList.add('tab-active', 'text-blue-600');
        document.getElementById('tab-batch').classList.remove('text-gray-500', 'border-transparent');
        document.getElementById('content-batch').classList.remove('hidden');
    }
}

// ============================================================================
// FORM HANDLING
// ============================================================================

function setupEventListeners() {
    document.getElementById('single-form').addEventListener('submit', handleSingleExtraction);
    document.getElementById('batch-form').addEventListener('submit', handleBatchExtraction);
}

function setDefaultDates() {
    const today = new Date();
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(today.getFullYear() - 1);

    const formatDate = (date) => date.toISOString().split('T')[0];

    document.getElementById('start-date').value = formatDate(oneYearAgo);
    document.getElementById('end-date').value = formatDate(today);
    document.getElementById('batch-start-date').value = formatDate(oneYearAgo);
    document.getElementById('batch-end-date').value = formatDate(today);
}

// ============================================================================
// SINGLE LOCATION EXTRACTION
// ============================================================================

async function handleSingleExtraction(e) {
    e.preventDefault();

    // Hide previous results
    document.getElementById('results-single').classList.add('hidden');

    // Show progress
    showProgress('single', 'Initializing extraction...');

    // Collect selected variables
    const selectedVariables = Array.from(
        document.querySelectorAll('input[name="variables"]:checked')
    ).map(checkbox => checkbox.value);

    // Ensure at least one variable is selected
    if (selectedVariables.length === 0) {
        alert('Please select at least one climate variable to extract');
        hideProgress('single');
        return;
    }

    const data = {
        location_name: document.getElementById('location-name').value,
        latitude: parseFloat(document.getElementById('latitude').value),
        longitude: parseFloat(document.getElementById('longitude').value),
        start_date: document.getElementById('start-date').value,
        end_date: document.getElementById('end-date').value,
        buffer_km: parseFloat(document.getElementById('buffer-km').value),
        variables: selectedVariables
    };

    try {
        updateProgress('single', 30, 'Fetching data from Google Earth Engine...');

        const response = await fetch(`${API_BASE_URL}/extract`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Extraction failed');
        }

        updateProgress('single', 70, 'Processing data...');

        const result = await response.json();

        updateProgress('single', 100, 'Complete!');
        setTimeout(() => hideProgress('single'), 500);

        displaySingleResults(result);
    } catch (error) {
        hideProgress('single');
        alert(`Error: ${error.message}`);
        console.error('Extraction error:', error);
    }
}

function displaySingleResults(result) {
    const resultsDiv = document.getElementById('results-single');
    const contentDiv = document.getElementById('results-content');

    // Build statistics cards dynamically based on available data
    let statsHtml = `
        <div class="grid grid-cols-3 gap-4 mb-6">
            <div class="bg-blue-50 p-4 rounded-lg">
                <div class="text-sm text-blue-600 font-medium">Location</div>
                <div class="text-lg font-semibold">${result.location}</div>
            </div>
            <div class="bg-green-50 p-4 rounded-lg">
                <div class="text-sm text-green-600 font-medium">Records Extracted</div>
                <div class="text-lg font-semibold">${result.records_extracted}</div>
            </div>
    `;

    // Add statistics for temperature if available
    if (result.temperature_range && result.temperature_range.temperature) {
        const tempStats = result.temperature_range.temperature;
        statsHtml += `
            <div class="bg-orange-50 p-4 rounded-lg">
                <div class="text-sm text-orange-600 font-medium">Temperature Range</div>
                <div class="text-lg font-semibold">${tempStats.min.toFixed(1)}°C - ${tempStats.max.toFixed(1)}°C</div>
            </div>
        `;
    }

    // Add statistics for precipitation if available
    if (result.temperature_range && result.temperature_range.precipitation) {
        const precipStats = result.temperature_range.precipitation;
        statsHtml += `
            <div class="bg-blue-100 p-4 rounded-lg">
                <div class="text-sm text-blue-700 font-medium">Precipitation</div>
                <div class="text-lg font-semibold">Total: ${precipStats.total.toFixed(1)} mm</div>
                <div class="text-sm text-gray-600">Mean: ${precipStats.mean.toFixed(1)} mm/day</div>
            </div>
        `;
    }

    // Add statistics for wind if available
    if (result.temperature_range && result.temperature_range.wind_speed) {
        const windStats = result.temperature_range.wind_speed;
        statsHtml += `
            <div class="bg-purple-50 p-4 rounded-lg">
                <div class="text-sm text-purple-600 font-medium">Wind Speed</div>
                <div class="text-lg font-semibold">Mean: ${windStats.mean.toFixed(1)} m/s</div>
                <div class="text-sm text-gray-600">Max: ${windStats.max.toFixed(1)} m/s</div>
            </div>
        `;
    }

    statsHtml += `</div>`;

    // Display summary statistics
    contentDiv.innerHTML = statsHtml + `
        <div class="mb-4">
            <button onclick="downloadSingleData()" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                📥 Download Data (JSON)
            </button>
        </div>
    `;

    resultsDiv.classList.remove('hidden');

    // Store data for download
    window.currentExtractionData = result;

    // Create chart with available data
    createClimateChart(result.data.daily);
}

function createClimateChart(data) {
    const ctx = document.getElementById('temperature-chart');

    // Destroy existing chart if any
    if (currentChart) {
        currentChart.destroy();
    }

    if (!data || data.length === 0) {
        return;
    }

    // Prepare data
    const dates = data.map(d => d.date);
    const datasets = [];

    // Detect available variables and create datasets
    const firstRecord = data[0];

    // Temperature datasets
    if ('tmax_celsius' in firstRecord) {
        datasets.push({
            label: 'Max Temperature (°C)',
            data: data.map(d => d.tmax_celsius),
            borderColor: 'rgb(239, 68, 68)',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            tension: 0.3,
            yAxisID: 'y'
        });
    }
    if ('tmean_celsius' in firstRecord) {
        datasets.push({
            label: 'Mean Temperature (°C)',
            data: data.map(d => d.tmean_celsius),
            borderColor: 'rgb(59, 130, 246)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.3,
            yAxisID: 'y'
        });
    }

    // Precipitation dataset
    if ('precipitation_mm' in firstRecord) {
        datasets.push({
            label: 'Precipitation (mm)',
            data: data.map(d => d.precipitation_mm),
            borderColor: 'rgb(14, 165, 233)',
            backgroundColor: 'rgba(14, 165, 233, 0.3)',
            type: 'bar',
            yAxisID: 'y1'
        });
    }

    // Wind speed dataset
    if ('wind_speed_ms' in firstRecord) {
        datasets.push({
            label: 'Wind Speed (m/s)',
            data: data.map(d => d.wind_speed_ms),
            borderColor: 'rgb(139, 92, 246)',
            backgroundColor: 'rgba(139, 92, 246, 0.1)',
            tension: 0.3,
            yAxisID: 'y2'
        });
    }

    // Humidity/Dewpoint dataset
    if ('dewpoint_celsius' in firstRecord) {
        datasets.push({
            label: 'Dewpoint (°C)',
            data: data.map(d => d.dewpoint_celsius),
            borderColor: 'rgb(34, 197, 94)',
            backgroundColor: 'rgba(34, 197, 94, 0.1)',
            tension: 0.3,
            yAxisID: 'y'
        });
    }

    // Configure scales based on available data
    const scales = {
        x: {
            display: true,
            title: { display: true, text: 'Date' },
            ticks: { maxTicksLimit: 10 }
        },
        y: {
            type: 'linear',
            display: true,
            position: 'left',
            title: { display: true, text: 'Temperature (°C)' }
        }
    };

    // Add secondary axis for precipitation if present
    if ('precipitation_mm' in firstRecord) {
        scales.y1 = {
            type: 'linear',
            display: true,
            position: 'right',
            title: { display: true, text: 'Precipitation (mm)' },
            grid: { drawOnChartArea: false }
        };
    }

    // Add tertiary axis for wind if present
    if ('wind_speed_ms' in firstRecord) {
        scales.y2 = {
            type: 'linear',
            display: datasets.length > 3,
            position: 'right',
            title: { display: true, text: 'Wind Speed (m/s)' },
            grid: { drawOnChartArea: false }
        };
    }

    currentChart = new Chart(ctx, {
        type: 'line',
        data: { labels: dates, datasets: datasets },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Climate Variables Time Series'
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: scales
        }
    });
}

function downloadSingleData() {
    if (!window.currentExtractionData) return;

    const dataStr = JSON.stringify(window.currentExtractionData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });

    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `climate_data_${window.currentExtractionData.location}_${new Date().toISOString().split('T')[0]}.json`;
    link.click();

    URL.revokeObjectURL(url);
}

// ============================================================================
// BATCH CSV EXTRACTION
// ============================================================================

async function handleBatchExtraction(e) {
    e.preventDefault();

    const fileInput = document.getElementById('csv-file');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select a CSV file');
        return;
    }

    showProgress('batch', 'Uploading CSV and processing locations...');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('start_date', document.getElementById('batch-start-date').value);
    formData.append('end_date', document.getElementById('batch-end-date').value);
    formData.append('buffer_km', document.getElementById('batch-buffer-km').value);

    try {
        updateProgress('batch', 30, 'Extracting data for all locations...');

        const response = await fetch(`${API_BASE_URL}/extract/batch`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Batch extraction failed');
        }

        updateProgress('batch', 90, 'Preparing download...');

        // Download the Excel file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `climate_data_batch_${new Date().toISOString().split('T')[0]}.xlsx`;
        link.click();
        window.URL.revokeObjectURL(url);

        updateProgress('batch', 100, 'Complete! File downloaded.');

        setTimeout(() => {
            hideProgress('batch');
            alert('Batch extraction completed successfully! Check your downloads folder.');
        }, 1000);

    } catch (error) {
        hideProgress('batch');
        alert(`Error: ${error.message}`);
        console.error('Batch extraction error:', error);
    }
}

// ============================================================================
// PROGRESS HANDLING
// ============================================================================

function showProgress(type, message) {
    document.getElementById(`progress-${type}`).classList.remove('hidden');
    updateProgress(type, 0, message);
}

function updateProgress(type, percent, message) {
    document.getElementById(`progress-bar-${type}`).style.width = `${percent}%`;
    document.getElementById(`progress-text-${type}`).textContent = message;
}

function hideProgress(type) {
    document.getElementById(`progress-${type}`).classList.add('hidden');
}

// ============================================================================
// SAMPLE CSV DOWNLOAD
// ============================================================================

function downloadSampleCSV() {
    const csvContent = `location_name,latitude,longitude
Soweto Clinic,-26.2678,27.8607
Johannesburg Hospital,-26.2041,28.0473
Cape Town Clinic,-33.9249,18.4241
Durban Hospital,-29.8587,31.0218
Pretoria Medical Center,-25.7479,28.2293`;

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'sample_locations.csv';
    link.click();
    window.URL.revokeObjectURL(url);
}

// ============================================================================
// LOCATION SEARCH (GEOCODING)
// ============================================================================

let searchTimeout;
let currentSearchResults = [];

function setupLocationSearch() {
    const searchInput = document.getElementById('location-search');
    const resultsDiv = document.getElementById('search-results');

    // Handle input with debouncing
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();

        // Clear previous timeout
        clearTimeout(searchTimeout);

        if (query.length < 3) {
            resultsDiv.classList.add('hidden');
            return;
        }

        // Debounce search by 500ms
        searchTimeout = setTimeout(() => {
            searchLocation(query);
        }, 500);
    });

    // Hide results when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !resultsDiv.contains(e.target)) {
            resultsDiv.classList.add('hidden');
        }
    });
}

async function searchLocation(query) {
    const resultsDiv = document.getElementById('search-results');

    try {
        // Use backend geocoding endpoint (Google Maps or Nominatim fallback)
        const url = `${API_BASE_URL}/geocode?query=${encodeURIComponent(query)}`;

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error('Geocoding request failed');
        }

        const data = await response.json();
        currentSearchResults = data.results || [];

        displaySearchResults(currentSearchResults);
    } catch (error) {
        console.error('Geocoding error:', error);
        resultsDiv.innerHTML = '<div class="p-3 text-red-600 text-sm">Search failed. Please try again.</div>';
        resultsDiv.classList.remove('hidden');
    }
}

function displaySearchResults(results) {
    const resultsDiv = document.getElementById('search-results');

    if (results.length === 0) {
        resultsDiv.innerHTML = '<div class="p-3 text-gray-600 text-sm">No results found. Try a different search term.</div>';
        resultsDiv.classList.remove('hidden');
        return;
    }

    // Build results HTML
    resultsDiv.innerHTML = results.map((result, index) => {
        const displayName = result.display_name;
        const type = result.type || 'location';

        return `
            <button type="button"
                    onclick="selectSearchResult(${index})"
                    class="w-full text-left p-3 hover:bg-blue-50 border-b border-gray-200 last:border-b-0 transition-colors">
                <div class="font-medium text-sm">${displayName}</div>
                <div class="text-xs text-gray-500 mt-1">
                    ${type.charAt(0).toUpperCase() + type.slice(1)} •
                    ${parseFloat(result.lat).toFixed(4)}, ${parseFloat(result.lon).toFixed(4)}
                </div>
            </button>
        `;
    }).join('');

    resultsDiv.classList.remove('hidden');
}

function selectSearchResult(index) {
    const result = currentSearchResults[index];

    if (!result) return;

    const lat = parseFloat(result.lat);
    const lon = parseFloat(result.lon);

    // Extract a clean location name
    let locationName = result.name || result.display_name.split(',')[0];

    // Update form fields
    document.getElementById('location-name').value = locationName;
    document.getElementById('latitude').value = lat.toFixed(4);
    document.getElementById('longitude').value = lon.toFixed(4);

    // Update map
    setMapLocation(lat, lon, locationName);

    // Clear search
    document.getElementById('location-search').value = '';
    document.getElementById('search-results').classList.add('hidden');

    // Show visual feedback
    const locationNameInput = document.getElementById('location-name');
    locationNameInput.classList.add('ring-2', 'ring-green-500');
    setTimeout(() => {
        locationNameInput.classList.remove('ring-2', 'ring-green-500');
    }, 1000);
}
