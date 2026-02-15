"""
Data quality validation for research integrity.

Ensures data meets quality standards before analysis.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from ..logger import get_logger

logger = get_logger()


@dataclass
class QualityReport:
    """Report of data quality checks."""

    passed: bool
    issues: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

    def __str__(self) -> str:
        """Format quality report for display."""
        status = "✓ PASSED" if self.passed else "✗ FAILED"
        report = [f"\n{'='*60}", f"DATA QUALITY REPORT - {status}", f"{'='*60}"]

        if self.issues:
            report.append("\n❌ Issues Found:")
            for issue in self.issues:
                report.append(f"  • {issue}")

        if self.warnings:
            report.append("\n⚠️  Warnings:")
            for warning in self.warnings:
                report.append(f"  • {warning}")

        if self.metadata:
            report.append("\n📊 Metadata:")
            for key, value in self.metadata.items():
                report.append(f"  {key}: {value}")

        report.append(f"{'='*60}\n")
        return "\n".join(report)


class DataQualityValidator:
    """
    Validates climate and health data quality.

    Critical for ensuring research reproducibility and reliability.
    """

    def __init__(self, strict: bool = False):
        """
        Initialize validator.

        Args:
            strict: If True, warnings are treated as failures
        """
        self.strict = strict

    def validate_climate_data(
        self,
        df: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> QualityReport:
        """
        Comprehensive validation of climate data.

        Args:
            df: DataFrame with climate data
            start_date: Expected start date (YYYY-MM-DD)
            end_date: Expected end date (YYYY-MM-DD)

        Returns:
            QualityReport with validation results
        """
        issues = []
        warnings = []
        metadata = {}

        logger.info("Validating climate data quality...")

        # Check 1: Required columns
        required_cols = ['date']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing required columns: {missing_cols}")

        # Check 2: Data completeness
        if 'date' in df.columns:
            gaps = self._check_date_gaps(df)
            if gaps:
                warnings.append(f"Found {len(gaps)} date gaps in time series")
                metadata['date_gaps'] = gaps[:5]  # First 5 gaps

        # Check 3: Missing values
        null_summary = self._check_missing_values(df)
        if null_summary:
            for col, pct in null_summary.items():
                if pct > 10:
                    issues.append(f"Column '{col}' has {pct:.1f}% missing values")
                elif pct > 0:
                    warnings.append(f"Column '{col}' has {pct:.1f}% missing values")

        # Check 4: Outliers
        if any('celsius' in col or 'temp' in col.lower() for col in df.columns):
            outlier_report = self._check_temperature_outliers(df)
            if outlier_report:
                metadata['outliers'] = outlier_report

        # Check 5: Date range validation
        if 'date' in df.columns and start_date and end_date:
            actual_start = df['date'].min()
            actual_end = df['date'].max()
            expected_start = pd.to_datetime(start_date)
            expected_end = pd.to_datetime(end_date)

            if actual_start > expected_start + timedelta(days=1):
                warnings.append(
                    f"Data starts {(actual_start - expected_start).days} days late"
                )
            if actual_end < expected_end - timedelta(days=1):
                warnings.append(
                    f"Data ends {(expected_end - actual_end).days} days early"
                )

        # Check 6: Duplicate dates
        if 'date' in df.columns:
            duplicates = df['date'].duplicated().sum()
            if duplicates > 0:
                issues.append(f"Found {duplicates} duplicate dates")

        # Metadata
        metadata['total_records'] = len(df)
        metadata['columns'] = list(df.columns)
        if 'date' in df.columns:
            metadata['date_range'] = (
                f"{df['date'].min().date()} to {df['date'].max().date()}"
            )

        # Determine pass/fail
        passed = len(issues) == 0 and (not self.strict or len(warnings) == 0)

        report = QualityReport(
            passed=passed,
            issues=issues,
            warnings=warnings,
            metadata=metadata
        )

        logger.info(f"Quality check {'passed' if passed else 'failed'}")
        return report

    def _check_date_gaps(self, df: pd.DataFrame) -> List[str]:
        """Find gaps in date sequence."""
        if 'date' not in df.columns:
            return []

        df_sorted = df.sort_values('date')
        dates = pd.to_datetime(df_sorted['date'])

        gaps = []
        for i in range(len(dates) - 1):
            diff = (dates.iloc[i + 1] - dates.iloc[i]).days
            if diff > 1:
                gaps.append(
                    f"{dates.iloc[i].date()} to {dates.iloc[i+1].date()} "
                    f"({diff-1} days)"
                )

        return gaps

    def _check_missing_values(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate percentage of missing values per column."""
        null_pct = (df.isnull().sum() / len(df) * 100).to_dict()
        return {col: pct for col, pct in null_pct.items() if pct > 0}

    def _check_temperature_outliers(
        self, df: pd.DataFrame
    ) -> Dict[str, Dict[str, int]]:
        """Check for temperature outliers."""
        outliers = {}

        temp_cols = [
            col for col in df.columns
            if 'celsius' in col or 'temp' in col.lower()
        ]

        for col in temp_cols:
            # Reasonable temperature range: -50°C to 60°C
            too_cold = (df[col] < -50).sum()
            too_hot = (df[col] > 60).sum()

            if too_cold > 0 or too_hot > 0:
                outliers[col] = {
                    'too_cold': too_cold,
                    'too_hot': too_hot
                }

        return outliers

    def validate_coordinates(
        self, lat: float, lon: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate geographic coordinates.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not -90 <= lat <= 90:
            return False, f"Invalid latitude: {lat} (must be -90 to 90)"

        if not -180 <= lon <= 180:
            return False, f"Invalid longitude: {lon} (must be -180 to 180)"

        # Check if coordinates are in ocean (simplified check)
        if abs(lat) < 0.01 and abs(lon) < 0.01:
            logger.warning("Coordinates very close to (0,0) - null island. Check validity.")

        return True, None

    def validate_date_range(
        self, start_date: str, end_date: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate date range for analysis.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)

            if end_dt <= start_dt:
                return False, "End date must be after start date"

            if start_dt > datetime.now():
                return False, "Start date cannot be in the future"

            duration = (end_dt - start_dt).days

            if duration < 1:
                return False, "Date range must be at least 1 day"

            if duration > 365 * 50:  # 50 years
                logger.warning(
                    f"Very long date range ({duration} days). "
                    "Consider using smaller chunks."
                )

            return True, None

        except Exception as e:
            return False, f"Invalid date format: {e}"

    def check_sample_size(
        self, n: int, min_required: int = 30
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if sample size is sufficient for statistical analysis.

        Args:
            n: Sample size
            min_required: Minimum required sample size

        Returns:
            Tuple of (is_sufficient, warning_message)
        """
        if n < min_required:
            return False, (
                f"Sample size ({n}) is below recommended minimum ({min_required}). "
                "Results may not be statistically robust."
            )

        return True, None
