"""
Data export functionality for climate data.

Handles exporting extracted climate data to various formats including
CSV, Excel, and creating visualizations.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from ..config import OutputConfig, get_config
from ..logger import LoggerMixin


class ClimateDataExporter(LoggerMixin):
    """
    Handles exporting climate data to various formats.

    Supports:
    - CSV export (daily and monthly)
    - Excel export with multiple sheets and metadata
    - Visualization generation
    """

    def __init__(self, config: Optional[OutputConfig] = None):
        """
        Initialize the data exporter.

        Args:
            config: Output configuration (uses global config if None)
        """
        self.config = config or get_config().output

    def export_data(
        self,
        daily_df: pd.DataFrame,
        monthly_df: pd.DataFrame,
        location_name: str,
        output_dir: Optional[Path] = None,
    ) -> List[Path]:
        """
        Export climate data to CSV and Excel formats.

        Args:
            daily_df: DataFrame with daily temperature data
            monthly_df: DataFrame with monthly temperature data
            location_name: Name of the location
            output_dir: Output directory (uses config default if None)

        Returns:
            List of created file paths
        """
        if daily_df.empty:
            self.logger.warning("No data to export")
            return []

        output_dir = output_dir or self.config.output_dir
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        created_files = []

        # Clean location name for filename
        clean_name = location_name.lower().replace(" ", "_").replace(",", "")

        # Get date range
        start_year = daily_df["date"].min().year
        end_year = daily_df["date"].max().year

        # Export CSV files
        if self.config.export_csv:
            csv_files = self._export_csv(
                daily_df, monthly_df, clean_name, start_year, end_year, output_dir
            )
            created_files.extend(csv_files)

        # Export Excel file
        if self.config.export_excel:
            excel_file = self._export_excel(
                daily_df,
                monthly_df,
                location_name,
                clean_name,
                start_year,
                end_year,
                output_dir,
            )
            if excel_file:
                created_files.append(excel_file)

        self.logger.info(f"Exported {len(created_files)} file(s)")
        for file_path in created_files:
            self.logger.info(f"  • {file_path}")

        return created_files

    def _export_csv(
        self,
        daily_df: pd.DataFrame,
        monthly_df: pd.DataFrame,
        clean_name: str,
        start_year: int,
        end_year: int,
        output_dir: Path,
    ) -> List[Path]:
        """Export data to CSV files."""
        created_files = []

        # Prepare daily data
        daily_export = daily_df[["date", "tmax_celsius", "tmean_celsius"]].copy()

        # Export daily CSV
        daily_csv = output_dir / f"{clean_name}_daily_temp_{start_year}_{end_year}.csv"
        daily_export.to_csv(daily_csv, index=False)
        created_files.append(daily_csv)
        self.logger.debug(f"Exported daily CSV: {daily_csv}")

        # Export monthly CSV if available
        if not monthly_df.empty:
            if "tmax_celsius_mean" in monthly_df.columns:
                monthly_export = monthly_df[
                    ["year_month", "tmax_celsius_mean", "tmean_celsius_mean"]
                ].copy()
                monthly_export.columns = ["month", "avg_tmax_celsius", "avg_tmean_celsius"]
            else:
                monthly_export = monthly_df.copy()

            monthly_csv = (
                output_dir / f"{clean_name}_monthly_temp_{start_year}_{end_year}.csv"
            )
            monthly_export.to_csv(monthly_csv, index=False)
            created_files.append(monthly_csv)
            self.logger.debug(f"Exported monthly CSV: {monthly_csv}")

        return created_files

    def _export_excel(
        self,
        daily_df: pd.DataFrame,
        monthly_df: pd.DataFrame,
        location_name: str,
        clean_name: str,
        start_year: int,
        end_year: int,
        output_dir: Path,
    ) -> Optional[Path]:
        """Export data to Excel file with multiple sheets."""
        try:
            excel_file = (
                output_dir / f"{clean_name}_temperature_data_{start_year}_{end_year}.xlsx"
            )

            # Prepare data for export
            daily_export = daily_df[["date", "tmax_celsius", "tmean_celsius"]].copy()

            with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
                # Export daily data
                daily_export.to_excel(writer, sheet_name="Daily_Data", index=False)

                # Export monthly data if available
                if not monthly_df.empty:
                    if "tmax_celsius_mean" in monthly_df.columns:
                        monthly_export = monthly_df[
                            ["year_month", "tmax_celsius_mean", "tmean_celsius_mean"]
                        ].copy()
                        monthly_export.columns = [
                            "month",
                            "avg_tmax_celsius",
                            "avg_tmean_celsius",
                        ]
                    else:
                        monthly_export = monthly_df.copy()

                    monthly_export.to_excel(
                        writer, sheet_name="Monthly_Averages", index=False
                    )

                # Add metadata sheet
                metadata = pd.DataFrame(
                    {
                        "Parameter": [
                            "Location",
                            "Date Range",
                            "Daily Records",
                            "Monthly Records",
                            "Min Temperature",
                            "Max Temperature",
                            "Data Source",
                            "Extraction Date",
                        ],
                        "Value": [
                            location_name,
                            f"{daily_df['date'].min().date()} to {daily_df['date'].max().date()}",
                            len(daily_export),
                            len(monthly_df) if not monthly_df.empty else 0,
                            f"{daily_df['tmean_celsius'].min():.1f}°C",
                            f"{daily_df['tmax_celsius'].max():.1f}°C",
                            "ERA5-Land (ECMWF)",
                            pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        ],
                    }
                )
                metadata.to_excel(writer, sheet_name="Metadata", index=False)

            self.logger.debug(f"Exported Excel file: {excel_file}")
            return excel_file

        except Exception as e:
            self.logger.error(f"Error exporting Excel file: {e}")
            return None

    def create_visualization(
        self,
        daily_df: pd.DataFrame,
        monthly_df: pd.DataFrame,
        location_name: str,
        output_dir: Optional[Path] = None,
        save_plot: bool = True,
    ) -> Optional[Path]:
        """
        Create comprehensive temperature visualizations.

        Args:
            daily_df: DataFrame with daily temperature data
            monthly_df: DataFrame with monthly temperature data
            location_name: Name of the location
            output_dir: Output directory (uses config default if None)
            save_plot: Whether to save the plot to file

        Returns:
            Path to saved plot file, or None if not saved
        """
        if daily_df.empty:
            self.logger.warning("No data to plot")
            return None

        self.logger.info("Creating temperature visualization")

        output_dir = output_dir or self.config.output_dir
        output_dir = Path(output_dir)

        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle(
            f"Temperature Analysis: {location_name}",
            fontsize=16,
            fontweight="bold",
        )

        # Plot 1: Daily time series
        axes[0, 0].plot(
            daily_df["date"],
            daily_df["tmax_celsius"],
            "r-",
            alpha=0.6,
            linewidth=0.5,
            label="Daily Max",
        )
        axes[0, 0].plot(
            daily_df["date"],
            daily_df["tmean_celsius"],
            "b-",
            alpha=0.6,
            linewidth=0.5,
            label="Daily Mean",
        )
        axes[0, 0].set_title("Daily Temperature Time Series", fontsize=12)
        axes[0, 0].set_ylabel("Temperature (°C)")
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        axes[0, 0].tick_params(axis="x", rotation=45)

        # Plot 2: Monthly averages
        if not monthly_df.empty and "date" in monthly_df.columns:
            axes[0, 1].plot(
                monthly_df["date"],
                monthly_df["tmax_celsius_mean"],
                "ro-",
                markersize=4,
                label="Monthly Avg Max",
            )
            axes[0, 1].plot(
                monthly_df["date"],
                monthly_df["tmean_celsius_mean"],
                "bo-",
                markersize=4,
                label="Monthly Avg Mean",
            )
            axes[0, 1].set_title("Monthly Average Temperatures", fontsize=12)
            axes[0, 1].set_ylabel("Temperature (°C)")
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
            axes[0, 1].tick_params(axis="x", rotation=45)
        else:
            axes[0, 1].text(
                0.5,
                0.5,
                "No monthly data available",
                ha="center",
                va="center",
                transform=axes[0, 1].transAxes,
            )
            axes[0, 1].set_title("Monthly Averages", fontsize=12)

        # Plot 3: Temperature distribution
        axes[1, 0].hist(
            daily_df["tmax_celsius"],
            bins=30,
            alpha=0.7,
            color="red",
            label="Max Temp",
            density=True,
        )
        axes[1, 0].hist(
            daily_df["tmean_celsius"],
            bins=30,
            alpha=0.7,
            color="blue",
            label="Mean Temp",
            density=True,
        )
        axes[1, 0].set_title("Temperature Distribution", fontsize=12)
        axes[1, 0].set_xlabel("Temperature (°C)")
        axes[1, 0].set_ylabel("Density")
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # Plot 4: Statistics summary
        stats_text = f"""Daily Temperature Statistics:

Max Temperature:
  Mean: {daily_df['tmax_celsius'].mean():.1f}°C
  Range: {daily_df['tmax_celsius'].min():.1f}°C to {daily_df['tmax_celsius'].max():.1f}°C
  Std Dev: {daily_df['tmax_celsius'].std():.1f}°C

Mean Temperature:
  Mean: {daily_df['tmean_celsius'].mean():.1f}°C
  Range: {daily_df['tmean_celsius'].min():.1f}°C to {daily_df['tmean_celsius'].max():.1f}°C
  Std Dev: {daily_df['tmean_celsius'].std():.1f}°C

Total Records: {len(daily_df)}
Date Range: {daily_df['date'].min().date()} to {daily_df['date'].max().date()}"""

        axes[1, 1].text(
            0.05,
            0.95,
            stats_text,
            transform=axes[1, 1].transAxes,
            verticalalignment="top",
            fontfamily="monospace",
            fontsize=10,
        )
        axes[1, 1].set_title("Summary Statistics", fontsize=12)
        axes[1, 1].axis("off")

        plt.tight_layout()

        plot_file = None
        if save_plot and self.config.export_plots:
            clean_name = location_name.lower().replace(" ", "_").replace(",", "")
            plot_file = output_dir / f"{clean_name}_temperature_analysis.png"
            plt.savefig(plot_file, dpi=self.config.plot_dpi, bbox_inches="tight")
            self.logger.info(f"Plot saved: {plot_file}")

        plt.close(fig)

        return plot_file
