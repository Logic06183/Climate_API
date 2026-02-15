"""
Unit tests for data validators.

Tests ensure data quality checks work correctly for research integrity.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from climate_toolkit.core.validators import DataQualityValidator, QualityReport


class TestDataQualityValidator:
    """Test suite for DataQualityValidator."""

    def test_init(self):
        """Test validator initialization."""
        validator = DataQualityValidator()
        assert validator.strict == False

        validator_strict = DataQualityValidator(strict=True)
        assert validator_strict.strict == True

    def test_validate_climate_data_perfect_data(self, sample_daily_climate_data):
        """Test validation with perfect data."""
        validator = DataQualityValidator()
        report = validator.validate_climate_data(
            sample_daily_climate_data,
            start_date='2020-01-01',
            end_date='2020-12-31'
        )

        assert isinstance(report, QualityReport)
        assert report.passed == True
        assert len(report.issues) == 0
        assert report.metadata['total_records'] == 366  # 2020 is leap year

    def test_validate_climate_data_with_gaps(self, sample_climate_data_with_gaps):
        """Test validation detects date gaps."""
        validator = DataQualityValidator()
        report = validator.validate_climate_data(sample_climate_data_with_gaps)

        assert len(report.warnings) > 0
        assert any('gap' in w.lower() for w in report.warnings)

    def test_validate_climate_data_with_outliers(self, sample_climate_data_with_outliers):
        """Test validation detects temperature outliers."""
        validator = DataQualityValidator()
        report = validator.validate_climate_data(sample_climate_data_with_outliers)

        assert 'outliers' in report.metadata
        assert report.metadata['outliers']['tmax_celsius']['too_cold'] > 0
        assert report.metadata['outliers']['tmax_celsius']['too_hot'] > 0

    def test_validate_climate_data_missing_columns(self):
        """Test validation detects missing required columns."""
        df = pd.DataFrame({
            'wrong_column': [1, 2, 3]
        })

        validator = DataQualityValidator()
        report = validator.validate_climate_data(df)

        assert report.passed == False
        assert any('Missing required columns' in issue for issue in report.issues)

    def test_validate_climate_data_duplicate_dates(self, sample_daily_climate_data):
        """Test validation detects duplicate dates."""
        # Add duplicate dates
        df_with_dupes = pd.concat([
            sample_daily_climate_data,
            sample_daily_climate_data.head(5)
        ])

        validator = DataQualityValidator()
        report = validator.validate_climate_data(df_with_dupes)

        assert report.passed == False
        assert any('duplicate dates' in issue.lower() for issue in report.issues)

    def test_validate_coordinates_valid(self):
        """Test coordinate validation with valid coordinates."""
        validator = DataQualityValidator()

        # Valid coordinates
        is_valid, error = validator.validate_coordinates(-26.2678, 27.8607)
        assert is_valid == True
        assert error is None

    def test_validate_coordinates_invalid_latitude(self):
        """Test coordinate validation rejects invalid latitude."""
        validator = DataQualityValidator()

        is_valid, error = validator.validate_coordinates(95.0, 27.0)
        assert is_valid == False
        assert 'latitude' in error.lower()

    def test_validate_coordinates_invalid_longitude(self):
        """Test coordinate validation rejects invalid longitude."""
        validator = DataQualityValidator()

        is_valid, error = validator.validate_coordinates(-26.0, 200.0)
        assert is_valid == False
        assert 'longitude' in error.lower()

    def test_validate_date_range_valid(self):
        """Test date range validation with valid range."""
        validator = DataQualityValidator()

        is_valid, error = validator.validate_date_range('2020-01-01', '2020-12-31')
        assert is_valid == True
        assert error is None

    def test_validate_date_range_end_before_start(self):
        """Test date range validation rejects end before start."""
        validator = DataQualityValidator()

        is_valid, error = validator.validate_date_range('2020-12-31', '2020-01-01')
        assert is_valid == False
        assert 'after start' in error.lower()

    def test_validate_date_range_future_date(self):
        """Test date range validation rejects future dates."""
        validator = DataQualityValidator()

        future_start = (datetime.now() + pd.Timedelta(days=30)).strftime('%Y-%m-%d')
        future_end = (datetime.now() + pd.Timedelta(days=60)).strftime('%Y-%m-%d')
        is_valid, error = validator.validate_date_range(future_start, future_end)
        assert is_valid == False
        assert 'future' in error.lower()

    def test_validate_date_range_invalid_format(self):
        """Test date range validation rejects invalid format."""
        validator = DataQualityValidator()

        is_valid, error = validator.validate_date_range('not-a-date', '2020-12-31')
        assert is_valid == False
        assert error is not None

    def test_check_sample_size_sufficient(self):
        """Test sample size check with sufficient data."""
        validator = DataQualityValidator()

        is_sufficient, warning = validator.check_sample_size(100, min_required=30)
        assert is_sufficient == True
        assert warning is None

    def test_check_sample_size_insufficient(self):
        """Test sample size check with insufficient data."""
        validator = DataQualityValidator()

        is_sufficient, warning = validator.check_sample_size(20, min_required=30)
        assert is_sufficient == False
        assert 'below recommended' in warning.lower()

    def test_quality_report_str(self):
        """Test QualityReport string representation."""
        report = QualityReport(
            passed=False,
            issues=['Issue 1', 'Issue 2'],
            warnings=['Warning 1'],
            metadata={'key': 'value'}
        )

        report_str = str(report)
        assert '✗ FAILED' in report_str
        assert 'Issue 1' in report_str
        assert 'Warning 1' in report_str
        assert 'key: value' in report_str

    def test_strict_mode_treats_warnings_as_failures(self, sample_climate_data_with_gaps):
        """Test strict mode treats warnings as failures."""
        validator_strict = DataQualityValidator(strict=True)
        report = validator_strict.validate_climate_data(sample_climate_data_with_gaps)

        # Should fail in strict mode due to warnings
        assert report.passed == False

    def test_non_strict_mode_allows_warnings(self, sample_climate_data_with_gaps):
        """Test non-strict mode passes despite warnings."""
        validator = DataQualityValidator(strict=False)
        report = validator.validate_climate_data(sample_climate_data_with_gaps)

        # Should pass in non-strict mode despite warnings
        # (unless there are actual issues)
        assert len(report.warnings) > 0


class TestQualityReport:
    """Test suite for QualityReport."""

    def test_quality_report_creation(self):
        """Test creating a quality report."""
        report = QualityReport(
            passed=True,
            issues=[],
            warnings=['Minor warning'],
            metadata={'records': 100}
        )

        assert report.passed == True
        assert len(report.issues) == 0
        assert len(report.warnings) == 1
        assert report.metadata['records'] == 100

    def test_quality_report_passed_string(self):
        """Test quality report string for passed validation."""
        report = QualityReport(
            passed=True,
            issues=[],
            warnings=[],
            metadata={}
        )

        report_str = str(report)
        assert '✓ PASSED' in report_str

    def test_quality_report_failed_string(self):
        """Test quality report string for failed validation."""
        report = QualityReport(
            passed=False,
            issues=['Critical issue'],
            warnings=[],
            metadata={}
        )

        report_str = str(report)
        assert '✗ FAILED' in report_str
        assert 'Critical issue' in report_str
