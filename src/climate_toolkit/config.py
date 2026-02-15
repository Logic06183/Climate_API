"""
Configuration management for Climate Toolkit.

Handles loading configuration from environment variables, config files,
and provides sensible defaults for all settings.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


@dataclass
class GEEConfig:
    """Google Earth Engine configuration."""

    project_id: Optional[str] = field(
        default_factory=lambda: os.getenv("GEE_PROJECT_ID")
    )
    credentials_path: Optional[Path] = field(
        default_factory=lambda: (
            Path(os.getenv("GEE_CREDENTIALS_PATH"))
            if os.getenv("GEE_CREDENTIALS_PATH")
            else None
        )
    )

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.credentials_path and not self.credentials_path.exists():
            raise ValueError(f"Credentials file not found: {self.credentials_path}")


@dataclass
class ExtractionConfig:
    """Configuration for data extraction."""

    # Default buffer radius around point locations (km)
    default_buffer_km: float = 10.0

    # Default chunk size for processing large time series (days)
    default_chunk_days: int = 90

    # Default scale for data extraction (meters)
    default_scale_m: int = 1000

    # Timeout for GEE API calls (seconds)
    api_timeout_seconds: int = 300

    # Maximum number of retry attempts
    max_retries: int = 3


@dataclass
class OutputConfig:
    """Configuration for data output."""

    # Default output directory
    output_dir: Path = field(default_factory=lambda: Path("./data"))

    # Export formats to generate
    export_csv: bool = True
    export_excel: bool = True
    export_plots: bool = True

    # Plot DPI for saved figures
    plot_dpi: int = 150

    def __post_init__(self) -> None:
        """Create output directory if it doesn't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"

    # Whether to log to file
    log_to_file: bool = False
    log_file: Optional[Path] = None

    def __post_init__(self) -> None:
        """Validate logging configuration."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level.upper() not in valid_levels:
            raise ValueError(
                f"Invalid log level: {self.level}. Must be one of {valid_levels}"
            )
        self.level = self.level.upper()


@dataclass
class ClimateToolkitConfig:
    """Main configuration container for Climate Toolkit."""

    gee: GEEConfig = field(default_factory=GEEConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_yaml(cls, config_path: Path) -> "ClimateToolkitConfig":
        """
        Load configuration from a YAML file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            ClimateToolkitConfig instance with loaded settings
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r") as f:
            config_dict = yaml.safe_load(f) or {}

        return cls(
            gee=GEEConfig(**config_dict.get("gee", {})),
            extraction=ExtractionConfig(**config_dict.get("extraction", {})),
            output=OutputConfig(**config_dict.get("output", {})),
            logging=LoggingConfig(**config_dict.get("logging", {})),
        )

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ClimateToolkitConfig":
        """
        Create configuration from a dictionary.

        Args:
            config_dict: Dictionary with configuration values

        Returns:
            ClimateToolkitConfig instance
        """
        return cls(
            gee=GEEConfig(**config_dict.get("gee", {})),
            extraction=ExtractionConfig(**config_dict.get("extraction", {})),
            output=OutputConfig(**config_dict.get("output", {})),
            logging=LoggingConfig(**config_dict.get("logging", {})),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration
        """
        from dataclasses import asdict
        return asdict(self)

    def save_yaml(self, output_path: Path) -> None:
        """
        Save configuration to YAML file.

        Args:
            output_path: Path where to save the YAML file
        """
        config_dict = self.to_dict()

        # Convert Path objects to strings for YAML serialization
        def convert_paths(obj: Any) -> Any:
            if isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_paths(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_paths(item) for item in obj]
            return obj

        config_dict = convert_paths(config_dict)

        with open(output_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)


# Global default configuration
_default_config: Optional[ClimateToolkitConfig] = None


def get_config() -> ClimateToolkitConfig:
    """
    Get the global configuration instance.

    Returns:
        The global ClimateToolkitConfig instance
    """
    global _default_config
    if _default_config is None:
        _default_config = ClimateToolkitConfig()
    return _default_config


def set_config(config: ClimateToolkitConfig) -> None:
    """
    Set the global configuration instance.

    Args:
        config: New configuration to use globally
    """
    global _default_config
    _default_config = config
