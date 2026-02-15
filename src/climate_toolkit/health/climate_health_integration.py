"""
Climate-Health Data Integration Module.

Specifically designed for epidemiological research on climate-sensitive health outcomes.
Optimized for Heat Centre research on heat exposure and pregnancy/cardiovascular outcomes.
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

from ..logger import LoggerMixin
from ..core.validators import DataQualityValidator


class ClimateHealthIntegrator(LoggerMixin):
    """
    Integrates climate and health data for epidemiological analysis.

    Optimized for:
    - Heat-health relationships
    - Temporal lag analysis
    - Pregnancy outcomes (preterm births, low birth weight)
    - Cardiovascular events
    - Infectious disease seasonality
    """

    def __init__(self, validate_data: bool = True):
        """
        Initialize integrator.

        Args:
            validate_data: Automatically validate data quality
        """
        self.validate_data = validate_data
        self.validator = DataQualityValidator() if validate_data else None

    def merge_climate_health(
        self,
        climate_df: pd.DataFrame,
        health_df: pd.DataFrame,
        time_column: str = 'date',
        lag_days: Optional[List[int]] = None,
    ) -> pd.DataFrame:
        """
        Merge climate and health data with temporal lags.

        Critical for climate-health analysis as health outcomes often lag
        exposure by days to weeks.

        Args:
            climate_df: Climate data with date column
            health_df: Health data with date column
            time_column: Name of date column (default: 'date')
            lag_days: Lag periods to test (default: [0, 7, 14, 21, 30])

        Returns:
            Merged DataFrame with lagged climate variables

        Example:
            # Merge heat exposure with preterm births
            merged = integrator.merge_climate_health(
                climate_df=temperature_data,
                health_df=birth_outcomes,
                lag_days=[0, 7, 14, 30]  # Test exposure windows
            )
        """
        if lag_days is None:
            lag_days = [0, 7, 14, 21, 30]

        self.logger.info(f"Merging climate-health data with lags: {lag_days}")

        # Ensure date columns are datetime
        climate_df = climate_df.copy()
        health_df = health_df.copy()
        climate_df[time_column] = pd.to_datetime(climate_df[time_column])
        health_df[time_column] = pd.to_datetime(health_df[time_column])

        # Start with health data
        merged = health_df.copy()

        # Add lagged climate variables
        climate_cols = [col for col in climate_df.columns if col != time_column]

        for lag in lag_days:
            self.logger.debug(f"Creating lag {lag} variables")

            # Shift climate data
            lagged_climate = climate_df.copy()
            lagged_climate[time_column] = lagged_climate[time_column] + pd.Timedelta(days=lag)

            # Rename columns to indicate lag
            lag_suffix = f"_lag{lag}" if lag > 0 else ""
            rename_dict = {
                col: f"{col}{lag_suffix}"
                for col in climate_cols
            }
            lagged_climate = lagged_climate.rename(columns=rename_dict)

            # Merge
            merged = merged.merge(
                lagged_climate,
                on=time_column,
                how='left'
            )

        self.logger.info(f"Merged data shape: {merged.shape}")
        self.logger.info(f"Added {len(lag_days) * len(climate_cols)} lagged climate variables")

        return merged

    def calculate_correlation_matrix(
        self,
        merged_df: pd.DataFrame,
        health_outcomes: List[str],
        climate_variables: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix between climate and health variables.

        Args:
            merged_df: Merged climate-health data
            health_outcomes: List of health outcome column names
            climate_variables: List of climate variable names (auto-detect if None)

        Returns:
            Correlation matrix DataFrame
        """
        if climate_variables is None:
            # Auto-detect climate variables (those with temperature or lag in name)
            climate_variables = [
                col for col in merged_df.columns
                if 'temp' in col.lower() or 'celsius' in col.lower() or 'lag' in col.lower()
            ]

        self.logger.info(f"Calculating correlations for {len(health_outcomes)} outcomes "
                        f"and {len(climate_variables)} climate variables")

        # Select relevant columns
        analysis_cols = health_outcomes + climate_variables
        analysis_df = merged_df[analysis_cols].dropna()

        # Calculate correlation matrix
        corr_matrix = analysis_df.corr()

        # Extract climate-health correlations
        climate_health_corr = corr_matrix.loc[climate_variables, health_outcomes]

        return climate_health_corr

    def analyze_heat_thresholds(
        self,
        merged_df: pd.DataFrame,
        temperature_col: str,
        health_outcome_col: str,
        thresholds: Optional[List[float]] = None,
    ) -> pd.DataFrame:
        """
        Analyze health outcomes at different heat thresholds.

        Critical for identifying heat wave impacts and vulnerable populations.

        Args:
            merged_df: Merged data
            temperature_col: Temperature column name
            health_outcome_col: Health outcome column name
            thresholds: Temperature thresholds in Celsius (default: [25, 28, 30, 32, 35])

        Returns:
            DataFrame with threshold analysis results
        """
        if thresholds is None:
            thresholds = [25, 28, 30, 32, 35]

        self.logger.info(f"Analyzing heat thresholds: {thresholds}")

        results = []

        for threshold in thresholds:
            # Days above threshold
            above_threshold = merged_df[temperature_col] >= threshold

            # Calculate outcomes
            outcome_above = merged_df.loc[above_threshold, health_outcome_col].mean()
            outcome_below = merged_df.loc[~above_threshold, health_outcome_col].mean()

            # Statistical test
            above_data = merged_df.loc[above_threshold, health_outcome_col].dropna()
            below_data = merged_df.loc[~above_threshold, health_outcome_col].dropna()

            if len(above_data) > 0 and len(below_data) > 0:
                t_stat, p_value = stats.ttest_ind(above_data, below_data)

                results.append({
                    'threshold_celsius': threshold,
                    'days_above': above_threshold.sum(),
                    'days_below': (~above_threshold).sum(),
                    'outcome_above_mean': outcome_above,
                    'outcome_below_mean': outcome_below,
                    'relative_risk': outcome_above / outcome_below if outcome_below > 0 else np.nan,
                    't_statistic': t_stat,
                    'p_value': p_value,
                    'significant': p_value < 0.05
                })

        results_df = pd.DataFrame(results)
        self.logger.info(f"Threshold analysis complete")

        return results_df

    def calculate_distributed_lag(
        self,
        merged_df: pd.DataFrame,
        exposure_col: str,
        outcome_col: str,
        max_lag: int = 30,
    ) -> pd.DataFrame:
        """
        Calculate distributed lag model for exposure-outcome relationship.

        Shows how the effect of exposure varies across different lag periods.

        Args:
            merged_df: Merged data
            exposure_col: Exposure variable (e.g., 'tmax_celsius')
            outcome_col: Health outcome variable
            max_lag: Maximum lag period in days

        Returns:
            DataFrame with lag coefficients
        """
        self.logger.info(f"Calculating distributed lag up to {max_lag} days")

        results = []

        for lag in range(max_lag + 1):
            # Create lagged exposure
            exposure_lagged = merged_df[exposure_col].shift(lag)
            outcome = merged_df[outcome_col]

            # Remove NaN
            valid_idx = ~(exposure_lagged.isna() | outcome.isna())
            x = exposure_lagged[valid_idx].values
            y = outcome[valid_idx].values

            if len(x) > 10:  # Minimum sample size
                # Calculate correlation
                corr, p_value = stats.pearsonr(x, y)

                results.append({
                    'lag_days': lag,
                    'correlation': corr,
                    'p_value': p_value,
                    'significant': p_value < 0.05,
                    'n_observations': len(x)
                })

        results_df = pd.DataFrame(results)
        return results_df

    def create_publication_table(
        self,
        threshold_results: pd.DataFrame,
        save_path: Optional[Path] = None,
    ) -> str:
        """
        Create publication-ready table of results.

        Args:
            threshold_results: Results from analyze_heat_thresholds
            save_path: Optional path to save table

        Returns:
            Formatted table string
        """
        # Format for publication
        table_data = threshold_results.copy()

        table_data['Threshold (°C)'] = table_data['threshold_celsius'].apply(lambda x: f"≥{x}")
        table_data['Days Exposed'] = table_data['days_above']
        table_data['Mean Outcome'] = table_data['outcome_above_mean'].apply(lambda x: f"{x:.2f}")
        table_data['Relative Risk'] = table_data['relative_risk'].apply(lambda x: f"{x:.2f}")
        table_data['P-value'] = table_data['p_value'].apply(
            lambda x: f"{x:.4f}" if x >= 0.001 else "<0.001"
        )
        table_data['Significance'] = table_data['significant'].apply(lambda x: "Yes" if x else "No")

        # Select columns for publication
        pub_table = table_data[[
            'Threshold (°C)', 'Days Exposed', 'Mean Outcome',
            'Relative Risk', 'P-value', 'Significance'
        ]]

        # Convert to string
        table_str = pub_table.to_string(index=False)

        if save_path:
            pub_table.to_csv(save_path, index=False)
            self.logger.info(f"Publication table saved to {save_path}")

        return table_str

    def plot_exposure_response(
        self,
        merged_df: pd.DataFrame,
        exposure_col: str,
        outcome_col: str,
        bins: int = 20,
        figsize: Tuple[int, int] = (10, 6),
    ) -> plt.Figure:
        """
        Create exposure-response curve plot.

        Shows relationship between climate exposure and health outcome.

        Args:
            merged_df: Merged data
            exposure_col: Exposure column name
            outcome_col: Outcome column name
            bins: Number of bins for exposure
            figsize: Figure size

        Returns:
            matplotlib Figure
        """
        self.logger.info("Creating exposure-response plot")

        # Create bins
        merged_df = merged_df.copy()
        merged_df['exposure_bin'] = pd.cut(
            merged_df[exposure_col],
            bins=bins
        )

        # Calculate mean outcome per bin
        binned = merged_df.groupby('exposure_bin').agg({
            outcome_col: ['mean', 'std', 'count'],
            exposure_col: 'mean'
        }).reset_index()

        binned.columns = ['bin', 'outcome_mean', 'outcome_std', 'n', 'exposure_mean']

        # Plot
        fig, ax = plt.subplots(figsize=figsize)

        ax.errorbar(
            binned['exposure_mean'],
            binned['outcome_mean'],
            yerr=binned['outcome_std'],
            fmt='o-',
            capsize=5,
            capthick=2,
            markersize=8
        )

        ax.set_xlabel(exposure_col.replace('_', ' ').title(), fontsize=12)
        ax.set_ylabel(outcome_col.replace('_', ' ').title(), fontsize=12)
        ax.set_title('Exposure-Response Relationship', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def generate_research_report(
        self,
        merged_df: pd.DataFrame,
        temperature_col: str,
        health_outcome_col: str,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive research report.

        Includes correlations, threshold analysis, and publication tables.

        Args:
            merged_df: Merged climate-health data
            temperature_col: Temperature column name
            health_outcome_col: Health outcome column name
            output_path: Optional path to save report

        Returns:
            Dictionary with all analysis results
        """
        self.logger.info("Generating comprehensive research report")

        report = {
            'metadata': {
                'n_observations': len(merged_df),
                'date_range': f"{merged_df['date'].min()} to {merged_df['date'].max()}",
                'temperature_variable': temperature_col,
                'health_outcome': health_outcome_col,
            }
        }

        # Correlation analysis
        self.logger.info("Calculating correlations...")
        corr, p_value = stats.pearsonr(
            merged_df[temperature_col].dropna(),
            merged_df[health_outcome_col].dropna()
        )
        report['correlation'] = {
            'pearson_r': corr,
            'p_value': p_value,
            'significant': p_value < 0.05
        }

        # Threshold analysis
        self.logger.info("Analyzing heat thresholds...")
        threshold_results = self.analyze_heat_thresholds(
            merged_df, temperature_col, health_outcome_col
        )
        report['threshold_analysis'] = threshold_results

        # Distributed lag
        self.logger.info("Calculating distributed lag...")
        lag_results = self.calculate_distributed_lag(
            merged_df, temperature_col, health_outcome_col
        )
        report['distributed_lag'] = lag_results

        # Publication table
        pub_table = self.create_publication_table(threshold_results)
        report['publication_table'] = pub_table

        if output_path:
            # Save report
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save tables
            threshold_results.to_csv(
                output_path.parent / f"{output_path.stem}_thresholds.csv",
                index=False
            )
            lag_results.to_csv(
                output_path.parent / f"{output_path.stem}_lags.csv",
                index=False
            )

            # Save summary
            with open(output_path, 'w') as f:
                f.write("CLIMATE-HEALTH RESEARCH REPORT\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Study Period: {report['metadata']['date_range']}\n")
                f.write(f"N Observations: {report['metadata']['n_observations']}\n")
                f.write(f"Temperature Variable: {temperature_col}\n")
                f.write(f"Health Outcome: {health_outcome_col}\n\n")
                f.write("CORRELATION ANALYSIS\n")
                f.write("-" * 60 + "\n")
                f.write(f"Pearson r: {report['correlation']['pearson_r']:.3f}\n")
                f.write(f"P-value: {report['correlation']['p_value']:.4f}\n")
                f.write(f"Significant: {report['correlation']['significant']}\n\n")
                f.write("HEAT THRESHOLD ANALYSIS\n")
                f.write("-" * 60 + "\n")
                f.write(pub_table)
                f.write("\n")

            self.logger.info(f"Report saved to {output_path}")

        return report
