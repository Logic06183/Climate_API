"""Offline tests for the exposure-window linkage logic (no Earth Engine)."""

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.bio_climate_link import (  # noqa: E402
    compute_exposure_windows,
    link_climate_dataframe,
)


def _synthetic_climate(start="2020-01-01", periods=120):
    """tmean_celsius equals the 1-based day index, so windows are predictable."""
    dates = pd.date_range(start=start, periods=periods, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "tmean_celsius": np.arange(1, periods + 1, dtype=float),
            "tmax_celsius": np.arange(1, periods + 1, dtype=float) + 5.0,
            "precipitation_mm": np.ones(periods, dtype=float),  # 1 mm/day
        }
    )


def test_same_day_and_window_means():
    climate = _synthetic_climate()
    # Jan 10 is day index 10.
    obs = pd.DataFrame({"_dt": pd.to_datetime(["2020-01-10"])})
    out = compute_exposure_windows(
        obs, climate, "_dt",
        value_cols=["tmean_celsius"],
        windows=[1, 7],
        aggregations={"tmean_celsius": ["mean", "min", "max"]},
    )
    row = out.iloc[0]
    # 1-day window == the day itself.
    assert row["tmean_celsius_mean_1d"] == pytest.approx(10.0)
    # 7-day window = days 4..10 -> mean 7, min 4, max 10.
    assert row["tmean_celsius_mean_7d"] == pytest.approx(7.0)
    assert row["tmean_celsius_min_7d"] == pytest.approx(4.0)
    assert row["tmean_celsius_max_7d"] == pytest.approx(10.0)
    # Same-day raw value column.
    assert row["tmean_celsius"] == pytest.approx(10.0)


def test_precipitation_sum():
    climate = _synthetic_climate()
    obs = pd.DataFrame({"_dt": pd.to_datetime(["2020-02-01"])})
    out = compute_exposure_windows(
        obs, climate, "_dt",
        value_cols=["precipitation_mm"],
        windows=[30],
    )
    # 1 mm/day over a 30-day window = 30 mm total.
    assert out.iloc[0]["precipitation_mm_sum_30d"] == pytest.approx(30.0)


def test_lag_shifts_window_back():
    climate = _synthetic_climate()
    obs = pd.DataFrame({"_dt": pd.to_datetime(["2020-01-20"])})
    # lag=10 -> window ends on Jan 10 (day 10). 1-day mean should be 10.
    out = compute_exposure_windows(
        obs, climate, "_dt",
        value_cols=["tmean_celsius"],
        windows=[1],
        lag=10,
    )
    assert out.iloc[0]["tmean_celsius_mean_1d"] == pytest.approx(10.0)


def test_coverage_partial_window():
    climate = _synthetic_climate(start="2020-01-05", periods=10)  # Jan 5..14 only
    obs = pd.DataFrame({"_dt": pd.to_datetime(["2020-01-07"])})
    out = compute_exposure_windows(
        obs, climate, "_dt",
        value_cols=["tmean_celsius"],
        windows=[7],
        add_coverage=True,
    )
    # Window Jan 1..7 requested but only Jan 5,6,7 exist -> 3/7 coverage.
    assert out.iloc[0]["coverage_7d"] == pytest.approx(3 / 7, abs=1e-4)
    assert out.iloc[0]["tmean_celsius_mean_7d_n"] == 3


def test_missing_date_yields_nan():
    climate = _synthetic_climate()
    obs = pd.DataFrame({"_dt": [pd.NaT]})
    out = compute_exposure_windows(
        obs, climate, "_dt", value_cols=["tmean_celsius"], windows=[7],
    )
    assert np.isnan(out.iloc[0]["tmean_celsius_mean_7d"])


def test_link_dataframe_groups_by_site_and_preserves_order():
    """End-to-end through link_climate_dataframe with an injected fetcher."""
    call_log = []

    def fake_fetch(lat, lon, start, end, variables, buffer_km):
        call_log.append((lat, lon))
        return _synthetic_climate(start="2019-12-01", periods=180)

    df = pd.DataFrame(
        {
            "sample_id": ["a", "b", "c"],
            "latitude": [-26.2000, -26.2000, -33.9000],  # a & b share a site
            "longitude": [28.0000, 28.0000, 18.4000],
            "date": ["2020-01-10", "2020-01-15", "2020-01-10"],
        }
    )
    out = link_climate_dataframe(
        df, variables=["temperature"], windows=[1, 7],
        fetch_fn=fake_fetch, progress=False,
    )
    # Two unique sites -> two fetches (not three rows).
    assert len(call_log) == 2
    # Original rows/order preserved.
    assert list(out["sample_id"]) == ["a", "b", "c"]
    assert len(out) == 3
    # Row a: Jan 10 -> day index relative to Dec 1 start. Dec has 31 days, so
    # Jan 10 = day 41. 1-day mean == 41.
    assert out.iloc[0]["tmean_celsius_mean_1d"] == pytest.approx(41.0)
