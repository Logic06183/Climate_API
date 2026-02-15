#!/bin/bash
# Launch the Climate-Health Analysis Web App

echo "🏥 Starting Climate-Health Analysis Platform..."
echo "=================================="
echo ""
echo "The app will open in your browser at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the app"
echo ""

cd "$(dirname "$0")"

# Install streamlit if needed
pip install streamlit 2>/dev/null

# Run the app
streamlit run climate_health_app.py
