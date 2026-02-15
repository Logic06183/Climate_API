# Climate Toolkit v0.2.0 🌍
## Professional Climate Data Extraction for Health Research

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A modern, production-ready Python toolkit for extracting climate data from Google Earth Engine, designed specifically for climate-health research.**

---

## 🎯 What's New in v0.2.0

- ✨ **Modern Python package** with proper structure and packaging
- 🎨 **Professional CLI** using Click for command-line operations
- ⚙️ **Configuration management** via YAML files and environment variables
- 📝 **Comprehensive logging** with configurable levels
- 🏗️ **Clean architecture** with separation of concerns
- 🔧 **Type hints** throughout the codebase
- 🧪 **Test-ready** structure for unit testing
- 📦 **Modular design** for easy extension

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd Climate_API

# Install the package in development mode
pip install -e .

# Or install with optional dependencies
pip install -e ".[dev,viz,geo]"

# Set up your GEE credentials
earthengine authenticate

# Create a configuration file
climate-extract init-config

# Edit .env file with your project ID
cp .env.example .env
# Edit .env and set GEE_PROJECT_ID
```

### Basic Usage (CLI)

```bash
# Extract climate data via command line
climate-extract extract \
    --lat -26.2678 \
    --lon 27.8607 \
    --start-date 2020-01-01 \
    --end-date 2020-12-31 \
    --location "Soweto, South Africa" \
    --output-dir ./data

# Test your GEE connection
climate-extract test-connection
```

### Basic Usage (Python API)

```python
from climate_toolkit import ClimateDataExtractor, ClimateDataExporter

# Initialize extractor
extractor = ClimateDataExtractor()

# Extract climate data
result = extractor.extract_climate_data(
    lat=-26.2678,
    lon=27.8607,
    start_date="2020-01-01",
    end_date="2020-12-31",
    location_name="Soweto, South Africa"
)

# Get the data
daily_df = result["daily"]
monthly_df = result["monthly"]

# Export data
exporter = ClimateDataExporter()
files = exporter.export_data(daily_df, monthly_df, "Soweto")
```

---

## 📁 New Repository Structure

```
Climate_API/
├── src/
│   └── climate_toolkit/          # Main package
│       ├── core/                  # Core extraction logic
│       │   ├── __init__.py
│       │   └── extractor.py       # ClimateDataExtractor class
│       ├── exporters/             # Data export functionality
│       │   ├── __init__.py
│       │   └── data_exporter.py   # ClimateDataExporter class
│       ├── utils/                 # Utility functions
│       ├── __init__.py
│       ├── config.py              # Configuration management
│       ├── logger.py              # Logging setup
│       └── cli.py                 # Command-line interface
├── examples/                      # Usage examples
│   ├── basic_extraction.py
│   └── multi_location_extraction.py
├── tests/                         # Unit tests (to be implemented)
├── data/                          # Output directory
├── docs/                          # Documentation
├── pyproject.toml                 # Modern Python packaging
├── .env.example                   # Example environment variables
├── .gitignore                     # Git ignore file
└── README.md                      # This file
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
GEE_PROJECT_ID=your-project-id
LOG_LEVEL=INFO
```

### Configuration File

Generate a configuration file:

```bash
climate-extract init-config
```

Edit `config.yaml`:

```yaml
gee:
  project_id: your-project-id

extraction:
  default_buffer_km: 10.0
  default_chunk_days: 90
  default_scale_m: 1000

output:
  output_dir: ./data
  export_csv: true
  export_excel: true
  export_plots: true
  plot_dpi: 150

logging:
  level: INFO
  log_to_file: false
```

Then use it:

```bash
climate-extract --config config.yaml extract [options]
```

---

## 🔧 CLI Commands

### Extract Climate Data

```bash
climate-extract extract \
    --lat -26.2678 \
    --lon 27.8607 \
    --start-date 2020-01-01 \
    --end-date 2020-12-31 \
    --location "Soweto" \
    --buffer-km 10 \
    --output-dir ./data
```

### Test GEE Connection

```bash
climate-extract test-connection --project-id your-project-id
```

### Initialize Configuration

```bash
climate-extract init-config --output my-config.yaml
```

### Global Options

```bash
climate-extract --help
climate-extract --version
climate-extract --log-level DEBUG extract [options]
```

---

## 📚 Examples

### Example 1: Basic Extraction

See `examples/basic_extraction.py`:

```python
from climate_toolkit import ClimateDataExtractor, ClimateDataExporter

extractor = ClimateDataExtractor()
result = extractor.extract_climate_data(
    lat=-26.2678, lon=27.8607,
    start_date="2020-01-01", end_date="2020-12-31",
    location_name="Soweto"
)
```

### Example 2: Multiple Locations

See `examples/multi_location_extraction.py`:

```python
locations = [
    {"name": "Johannesburg", "lat": -26.2041, "lon": 28.0473},
    {"name": "Cape Town", "lat": -33.9249, "lon": 18.4241},
]

for loc in locations:
    result = extractor.extract_climate_data(**loc, ...)
```

---

## 🏥 Use Cases

This toolkit is designed for:

- 🌡️ Studying heat stress and pregnancy outcomes
- 💓 Analyzing temperature-cardiovascular relationships
- 📊 Seasonal climate-health pattern analysis
- 🔬 Climate extremes and mortality studies
- 🌍 Environmental epidemiology research

---

## 🌍 Data Sources

- **ERA5-Land**: High-quality atmospheric reanalysis (1979-present)
- **MODIS**: (Coming soon)
- **CHIRPS**: (Coming soon)
- **TerraClimate**: (Coming soon)

---

## 🧪 Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
pytest --cov=climate_toolkit
```

### Code Formatting

```bash
black src/
isort src/
flake8 src/
```

### Type Checking

```bash
mypy src/
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

- 📖 [Documentation](docs/getting_started.md)
- 🐛 [Issue Tracker](https://github.com/yourusername/climate-toolkit/issues)
- 💬 [Discussions](https://github.com/yourusername/climate-toolkit/discussions)

---

## ✨ Migration from v0.1.x

If you're upgrading from the old version:

**Old way:**
```python
# Old procedural script
from src.climate_utils import ClimateDataExtractor
extractor = ClimateDataExtractor()
# Manual initialization, extraction, export...
```

**New way:**
```python
# Modern package import
from climate_toolkit import ClimateDataExtractor, ClimateDataExporter

# or use the CLI
climate-extract extract --lat -26.2678 --lon 27.8607 ...
```

---

## 🙏 Acknowledgments

Developed by the **Heat Centre Research Team** as a contribution to the climate-health research community.

---

*Making climate data accessible for health researchers worldwide* 🌍
