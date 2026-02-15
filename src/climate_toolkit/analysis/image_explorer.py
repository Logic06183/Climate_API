"""
Interactive geospatial image explorer with AI capabilities.

Provides research-grade image analysis and visualization for satellite imagery.
"""

from pathlib import Path
from typing import Optional, List, Tuple, Union, Dict, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import rasterio
from rasterio.plot import show
from PIL import Image

from ..logger import LoggerMixin
from ..core.validators import DataQualityValidator

try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False


class ImageExplorer(LoggerMixin):
    """
    Interactive explorer for geospatial images.

    Features:
    - Multi-band satellite imagery support
    - Interactive band visualization
    - Statistical analysis per band
    - Geospatial metadata extraction
    - Export to various formats
    """

    def __init__(self):
        """Initialize the image explorer."""
        self.image: Optional[np.ndarray] = None
        self.metadata: Dict[str, Any] = {}
        self.bands: List[np.ndarray] = []
        self.transform: Optional[Any] = None
        self.crs: Optional[Any] = None
        self.filepath: Optional[Path] = None

    def load_image(self, filepath: Union[str, Path]) -> Dict[str, Any]:
        """
        Load a geospatial image with automatic format detection.

        Supports GeoTIFF, PNG, JPG, and other common formats.

        Args:
            filepath: Path to image file

        Returns:
            Dictionary with image metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be read
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Image file not found: {filepath}")

        self.filepath = filepath
        self.logger.info(f"Loading image: {filepath.name}")

        # Try geospatial raster first (GeoTIFF)
        try:
            metadata = self._load_geotiff(filepath)
            self.logger.info(
                f"✓ Loaded {self.image.shape[0]}-band GeoTIFF "
                f"({self.image.shape[1]}x{self.image.shape[2]} pixels)"
            )
            return metadata

        except Exception as e:
            self.logger.debug(f"Not a GeoTIFF, trying standard image: {e}")

        # Fall back to standard image
        try:
            metadata = self._load_standard_image(filepath)
            self.logger.info(
                f"✓ Loaded {self.image.shape[0]}-band image "
                f"({self.image.shape[1]}x{self.image.shape[2]} pixels)"
            )
            return metadata

        except Exception as e:
            raise ValueError(f"Could not load image: {e}") from e

    def _load_geotiff(self, filepath: Path) -> Dict[str, Any]:
        """Load GeoTIFF with geospatial metadata."""
        with rasterio.open(filepath) as src:
            # Read all bands
            self.image = src.read()  # Shape: (bands, height, width)
            self.metadata = dict(src.meta)
            self.transform = src.transform
            self.crs = src.crs
            self.bands = [src.read(i + 1) for i in range(src.count)]

            # Extract metadata
            metadata = {
                'format': 'GeoTIFF',
                'bands': src.count,
                'shape': self.image.shape,
                'crs': str(self.crs),
                'bounds': src.bounds,
                'resolution': (src.res[0], src.res[1]),
                'nodata': src.nodata,
            }

            return metadata

    def _load_standard_image(self, filepath: Path) -> Dict[str, Any]:
        """Load standard image format (PNG, JPG, etc.)."""
        img = Image.open(filepath)
        img_array = np.array(img)

        # Convert to (bands, height, width) format
        if len(img_array.shape) == 2:
            # Grayscale
            self.image = img_array[np.newaxis, :, :]
        else:
            # Color (transpose from HWC to CHW)
            self.image = np.transpose(img_array, (2, 0, 1))

        self.bands = [self.image[i] for i in range(self.image.shape[0])]

        metadata = {
            'format': 'Standard Image',
            'bands': self.image.shape[0],
            'shape': self.image.shape,
            'mode': img.mode,
        }

        return metadata

    def get_band_statistics(self, band_index: int = 0) -> pd.DataFrame:
        """
        Calculate comprehensive statistics for a band.

        Args:
            band_index: Index of band to analyze (0-based)

        Returns:
            DataFrame with statistics

        Raises:
            ValueError: If band index invalid or no image loaded
        """
        if self.image is None:
            raise ValueError("No image loaded. Use load_image() first.")

        if not 0 <= band_index < self.image.shape[0]:
            raise ValueError(
                f"Invalid band index: {band_index}. "
                f"Valid range: 0-{self.image.shape[0]-1}"
            )

        band = self.image[band_index]

        # Calculate statistics
        stats = {
            'Band': band_index,
            'Min': float(np.nanmin(band)),
            'Max': float(np.nanmax(band)),
            'Mean': float(np.nanmean(band)),
            'Median': float(np.nanmedian(band)),
            'Std Dev': float(np.nanstd(band)),
            'Percentile 2': float(np.nanpercentile(band, 2)),
            'Percentile 98': float(np.nanpercentile(band, 98)),
            'Valid Pixels': int(np.count_nonzero(~np.isnan(band))),
            'Null Pixels': int(np.count_nonzero(np.isnan(band))),
        }

        self.logger.info(f"Band {band_index} statistics calculated")
        return pd.DataFrame([stats])

    def get_all_band_statistics(self) -> pd.DataFrame:
        """
        Get statistics for all bands.

        Returns:
            DataFrame with statistics for each band
        """
        if self.image is None:
            raise ValueError("No image loaded")

        stats_list = []
        for i in range(self.image.shape[0]):
            stats = self.get_band_statistics(i).iloc[0].to_dict()
            stats_list.append(stats)

        df = pd.DataFrame(stats_list)
        self.logger.info(f"Statistics calculated for {len(stats_list)} bands")
        return df

    def _normalize_band(
        self, band: np.ndarray, percentile_clip: bool = True
    ) -> np.ndarray:
        """
        Normalize band for display.

        Args:
            band: Band array
            percentile_clip: Use 2-98 percentile clipping (robust to outliers)

        Returns:
            Normalized band (0-1 range)
        """
        if percentile_clip:
            p2 = np.nanpercentile(band, 2)
            p98 = np.nanpercentile(band, 98)
            clipped = np.clip(band, p2, p98)
        else:
            clipped = band

        # Normalize to 0-1
        min_val = np.nanmin(clipped)
        max_val = np.nanmax(clipped)

        if max_val > min_val:
            normalized = (clipped - min_val) / (max_val - min_val)
        else:
            normalized = clipped

        return np.nan_to_num(normalized, 0)

    def show_rgb(
        self,
        r_band: int = 0,
        g_band: int = 1,
        b_band: int = 2,
        figsize: Tuple[int, int] = (12, 8),
        title: Optional[str] = None,
    ) -> plt.Figure:
        """
        Display RGB composite.

        Args:
            r_band: Red band index
            g_band: Green band index
            b_band: Blue band index
            figsize: Figure size
            title: Plot title

        Returns:
            matplotlib Figure object
        """
        if self.image is None:
            raise ValueError("No image loaded")

        if self.image.shape[0] < 3:
            raise ValueError("Image must have at least 3 bands for RGB composite")

        # Create RGB composite
        rgb = np.stack([
            self._normalize_band(self.image[r_band]),
            self._normalize_band(self.image[g_band]),
            self._normalize_band(self.image[b_band]),
        ], axis=-1)

        # Plot
        fig, ax = plt.subplots(figsize=figsize)
        ax.imshow(rgb)
        ax.axis('off')

        if title is None:
            title = f"RGB Composite (R={r_band}, G={g_band}, B={b_band})"
        ax.set_title(title, fontsize=14, fontweight='bold')

        plt.tight_layout()
        self.logger.info(f"Displayed RGB composite")

        return fig

    def show_band(
        self,
        band_index: int = 0,
        cmap: str = 'viridis',
        figsize: Tuple[int, int] = (10, 8),
    ) -> plt.Figure:
        """
        Display single band with colorbar.

        Args:
            band_index: Band to display
            cmap: Colormap name
            figsize: Figure size

        Returns:
            matplotlib Figure object
        """
        if self.image is None:
            raise ValueError("No image loaded")

        band = self.image[band_index]

        fig, ax = plt.subplots(figsize=figsize)
        im = ax.imshow(band, cmap=cmap)
        plt.colorbar(im, ax=ax, label='Value')
        ax.set_title(f"Band {band_index}", fontsize=14, fontweight='bold')
        ax.axis('off')

        plt.tight_layout()
        return fig

    def export_stats(self, output_path: Union[str, Path]) -> Path:
        """
        Export band statistics to CSV.

        Args:
            output_path: Output file path

        Returns:
            Path to saved file
        """
        stats_df = self.get_all_band_statistics()
        output_path = Path(output_path)

        stats_df.to_csv(output_path, index=False)
        self.logger.info(f"Statistics exported to: {output_path}")

        return output_path

    def create_map(self, zoom_start: int = 10) -> Optional[Any]:
        """
        Create interactive map (requires folium and geospatial metadata).

        Args:
            zoom_start: Initial zoom level

        Returns:
            folium Map object or None if not geospatial
        """
        if not FOLIUM_AVAILABLE:
            self.logger.warning("folium not installed. Cannot create map.")
            return None

        if self.crs is None or self.transform is None:
            self.logger.warning("No geospatial metadata. Cannot create map.")
            return None

        # Calculate center point
        bounds = rasterio.open(self.filepath).bounds
        center_lat = (bounds.bottom + bounds.top) / 2
        center_lon = (bounds.left + bounds.right) / 2

        # Create map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_start,
            tiles='OpenStreetMap'
        )

        # Add image bounds
        folium.Rectangle(
            bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
            color='red',
            fill=False,
            popup=f"Image: {self.filepath.name}"
        ).add_to(m)

        self.logger.info("Interactive map created")
        return m
