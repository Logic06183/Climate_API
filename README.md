# Heat Centre Climate Data Toolkit
## Enabling Climate Data Access for Health Researchers

**A professional toolkit developed by the Heat Centre as a contribution to the health research consortium for extracting and analyzing climate data using Google Earth Engine (GEE) and GEEMAP.**

---

## 🏥 About This Tool

This repository provides **production-ready Python scripts** for health researchers to extract climate data from satellite datasets and integrate it with epidemiological studies. Specifically designed for studying climate-health relationships such as:

- **Heat stress and pregnancy outcomes** (preterm births, low birth weight)
- **Temperature variability and cardiovascular events**
- **Seasonal climate patterns and infectious disease**
- **Climate extremes and mortality studies**

## 🎯 Heat Centre Consortium Contribution

Developed as the **Heat Centre's contribution** to enabling accessible, reproducible climate data extraction for health researchers worldwide. This tool eliminates technical barriers and provides students and researchers with **debug-free, tested workflows** for climate-health research.

## ✨ Key Features

- **🔧 Production Ready**: Fully tested, debug-free scripts requiring no troubleshooting
- **📊 Health-Focused**: Examples and analyses designed for climate-health research
- **🌍 Scalable**: Handles datasets from months to decades with chunked processing
- **📁 Multiple Formats**: Export to CSV, Excel, and visualization outputs
- **🎓 Student-Friendly**: Clear documentation for researchers new to climate data
- **🚀 Consortium Ready**: Professional tool for sharing across research institutions

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

## 📁 Repository Structure

```
Climate_API/
├── scripts/                              # Production-ready Python scripts
│   ├── 01_basic_temperature_extraction_working.py  # Basic climate data extraction
│   └── case_study_soweto_working.py                # Soweto health research case study
├── src/                                    # Core utility functions
│   ├── climate_extraction.py              # Main extraction functions
│   ├── data_processing.py                 # Data cleaning and analysis
│   └── visualization.py                   # Plotting and mapping functions
├── data/                                   # Exported datasets (created after extraction)
│   └── soweto_south_africa_*              # Example: Full 6-year Soweto dataset
├── docs/                                   # Documentation and guides
│   ├── gee_setup.md                       # Google Earth Engine setup
│   ├── data_sources.md                    # Available climate datasets
│   └── health_examples.md                 # Health research applications
├── extract_climate_data.py                # Command-line extraction tool
├── test_gee_connection.py                 # Connection diagnostic tool
├── requirements.txt                       # Python dependencies
└── README.md                              # This documentation
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
