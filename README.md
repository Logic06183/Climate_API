# GEEMAP Climate Data for Health Analysis

A comprehensive repository to help students and researchers use GEEMAP (Google Earth Engine Python API) to extract climate data for health analyses.

## 🎯 Purpose

This repository provides tools and examples for:
- Extracting climate data (temperature, precipitation, etc.) using Google Earth Engine
- Processing climate data for health research applications
- Performing time series analysis with health outcomes
- Creating visualizations for climate-health relationships

## 🚀 Quick Start

### Prerequisites
1. Google Earth Engine account (sign up at [earthengine.google.com](https://earthengine.google.com))
2. Python 3.8+ with conda or pip

### Installation
```bash
# Clone this repository
git clone <your-repo-url>
cd Climate_API

# Install dependencies
pip install -r requirements.txt

# Authenticate with Google Earth Engine
earthengine authenticate
```

## 📚 Tutorials

### 1. Basic Climate Data Extraction
- `01_basic_temperature_extraction.ipynb` - Extract temperature data for a location
- `02_multi_location_analysis.ipynb` - Extract data for multiple locations
- `03_export_to_csv.ipynb` - Export climate data to CSV/Excel formats

### 2. Health Data Integration
- `04_health_climate_correlation.ipynb` - Correlate health outcomes with climate data
- `05_time_series_analysis.ipynb` - Seasonal decomposition and trend analysis
- `06_advanced_visualization.ipynb` - Create publication-ready plots

### 3. Case Studies
- `case_study_soweto.ipynb` - Preterm births vs temperature in Soweto (2016-2022)

## 📖 Documentation

- [Getting Started Guide](docs/getting_started.md)
- [API Reference](docs/api_reference.md)
- [Data Sources](docs/data_sources.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🗂️ Repository Structure

```
Climate_API/
├── notebooks/           # Jupyter notebooks with examples
├── src/                # Python modules and utilities
├── data/               # Sample datasets
├── docs/               # Documentation
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🌍 Supported Data Sources

- **ERA5 Reanalysis**: High-quality atmospheric reanalysis data
- **MODIS**: Satellite-based temperature and vegetation data
- **CHIRPS**: Precipitation data for climate hazards
- **TerraClimate**: Global climate and water balance data

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- Check the [Troubleshooting Guide](docs/troubleshooting.md)
- Open an issue for bugs or feature requests
- Join our discussions for questions and tips

## 🏥 Health Research Applications

This toolkit is particularly useful for:
- Studying climate-sensitive health outcomes
- Analyzing seasonal patterns in disease occurrence
- Investigating temperature-health relationships
- Creating evidence for climate adaptation strategies

---

*Developed to support climate-health research and education*
