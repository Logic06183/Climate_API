#!/bin/bash

# Quick start script for Climate-Health Data Extraction App

echo "🌍 Climate-Health Data Extraction Tool"
echo "======================================"
echo ""

# Check if we're in the webapp directory
if [ ! -f "backend/main.py" ]; then
    echo "❌ Error: Please run this script from the webapp directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r backend/requirements.txt

# Check Earth Engine authentication
echo ""
echo "🔐 Checking Earth Engine authentication..."
python3 -c "import ee; ee.Initialize(project='joburg-hvi'); print('✅ Earth Engine authenticated')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Earth Engine authentication may not be configured"
    echo "   Run: earthengine authenticate --force"
fi

echo ""
echo "🚀 Starting application..."
echo "   Access at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
cd backend && python3 main.py
