"""Stress tests for messy real-world inputs, using a deterministic fake fetcher
so we exercise the linkage logic without Earth Engine latency/flakiness."""

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.bio_climate_link import link_climate_dataframe  # noqa: E402


def make_fetcher(periods=800, start="2018-06-01"):
    """tmean = day index; records every call so we can assert per-site fetches."""
    calls = []

    def fetch(lat, lon, s, e, variables, buffer_km):
        calls.append((lat, lon, s, e, tuple(variables), buffer_km))
        dates = pd.date_range(start=start, periods=periods, freq="D")
        base = np.arange(1, periods + 1, dtype=float)
        cols = {"date": dates}
        if "temperature" in variables:
            cols["tmax_celsius"] = base + 5
            cols["tmean_celsius"] = base
        if "precipitation" in variables:
            cols["precipitation_mm"] = np.ones(periods)
        if "wind" in variables:
            cols["wind_speed_ms"] = base / 10
            cols["wind_u_ms"] = base / 20
            cols["wind_v_ms"] = base / 20
        return pd.DataFrame(cols)

    fetch.calls = calls
    return fetch


def test_custom_column_names_and_string_dates():
    f = make_fetcher()
    df = pd.DataFrame({
        "site": ["x", "y"],
        "lat": [-26.2, -26.2],
        "lon": [28.0, 28.0],
        "event_date": ["2020-01-10", "2020-02-15"],  # strings, not datetimes
    })
    out = link_climate_dataframe(
        df, lat_col="lat", lon_col="lon", date_col="event_date",
        variables=["temperature"], windows=[7], fetch_fn=f, progress=False,
    )
    assert "tmean_celsius_mean_7d" in out.columns
    assert out["tmean_celsius_mean_7d"].notna().all()
    assert len(f.calls) == 1  # one site


def test_messy_dates_do_not_crash_and_isolate_to_their_rows():
    f = make_fetcher()
    df = pd.DataFrame({
        "id": [1, 2, 3, 4],
        "latitude": [-26.2, -26.2, -26.2, -26.2],
        "longitude": [28.0, 28.0, 28.0, 28.0],
        "date": ["2020-01-10", None, "not-a-date", "2020-03-01"],
    })
    out = link_climate_dataframe(
        df, variables=["temperature"], windows=[30], fetch_fn=f, progress=False,
    )
    # Rows 1 and 4 have valid dates -> value; rows 2,3 -> NaN, no exception.
    assert out.loc[out["id"] == 1, "tmean_celsius_mean_30d"].notna().all()
    assert out.loc[out["id"] == 4, "tmean_celsius_mean_30d"].notna().all()
    assert out.loc[out["id"] == 2, "tmean_celsius_mean_30d"].isna().all()
    assert out.loc[out["id"] == 3, "tmean_celsius_mean_30d"].isna().all()
    assert list(out["id"]) == [1, 2, 3, 4]  # order preserved


def test_all_dates_missing_site_returns_nan_without_fetch():
    f = make_fetcher()
    df = pd.DataFrame({
        "latitude": [-26.2], "longitude": [28.0], "date": [None],
    })
    out = link_climate_dataframe(
        df, variables=["temperature"], windows=[7], fetch_fn=f, progress=False,
    )
    assert np.isnan(out["tmean_celsius_mean_7d"].iloc[0])
    assert len(f.calls) == 0  # no usable dates -> never hits the backend


def test_extra_columns_and_row_order_preserved_across_sites():
    f = make_fetcher()
    df = pd.DataFrame({
        "sample_id": ["s1", "s2", "s3", "s4"],
        "notes": ["a", "b", "c", "d"],
        "latitude": [-26.2, -33.9, -26.2, -29.8],
        "longitude": [28.0, 18.4, 28.0, 31.0],
        "date": ["2020-01-10", "2020-01-11", "2020-01-12", "2020-01-13"],
    })
    out = link_climate_dataframe(
        df, variables=["temperature"], windows=[7], fetch_fn=f, progress=False,
    )
    assert list(out["sample_id"]) == ["s1", "s2", "s3", "s4"]
    assert list(out["notes"]) == ["a", "b", "c", "d"]
    # 3 unique sites (s1 & s3 share) -> 3 fetches.
    assert len(f.calls) == 3


def test_wind_multi_column_output():
    f = make_fetcher()
    df = pd.DataFrame({
        "latitude": [-26.2], "longitude": [28.0], "date": ["2020-02-01"],
    })
    out = link_climate_dataframe(
        df, variables=["wind"], windows=[7], fetch_fn=f, progress=False,
    )
    assert "wind_speed_ms_mean_7d" in out.columns
    assert "wind_speed_ms_max_7d" in out.columns


def test_lag_excludes_recent_days():
    f = make_fetcher()
    df = pd.DataFrame({
        "latitude": [-26.2], "longitude": [28.0], "date": ["2020-03-01"],
    })
    no_lag = link_climate_dataframe(
        df, variables=["temperature"], windows=[7], lag=0,
        fetch_fn=f, progress=False)
    lagged = link_climate_dataframe(
        df, variables=["temperature"], windows=[7], lag=7,
        fetch_fn=f, progress=False)
    # Lagged window looks at earlier (cooler, lower day-index) days -> lower mean.
    assert lagged["tmean_celsius_mean_7d"].iloc[0] < no_lag["tmean_celsius_mean_7d"].iloc[0]


def test_backend_failure_for_one_site_does_not_sink_the_run():
    calls = []

    def flaky(lat, lon, s, e, variables, buffer_km):
        calls.append((lat, lon))
        if lat == -33.9:  # simulate a failed fetch for one site
            raise RuntimeError("simulated GEE outage")
        dates = pd.date_range(start="2019-06-01", periods=800, freq="D")
        return pd.DataFrame({"date": dates,
                             "tmax_celsius": np.arange(800) + 5.0,
                             "tmean_celsius": np.arange(800, dtype=float)})

    df = pd.DataFrame({
        "id": ["ok", "bad"],
        "latitude": [-26.2, -33.9],
        "longitude": [28.0, 18.4],
        "date": ["2020-01-10", "2020-01-10"],
    })
    out = link_climate_dataframe(
        df, variables=["temperature"], windows=[7], fetch_fn=flaky, progress=False,
    )
    assert out.loc[out["id"] == "ok", "tmean_celsius_mean_7d"].notna().all()
    assert out.loc[out["id"] == "bad", "tmean_celsius_mean_7d"].isna().all()
    assert len(out) == 2  # run completed despite one site failing


def test_unknown_variable_raises_clear_error():
    df = pd.DataFrame({"latitude": [-26.2], "longitude": [28.0], "date": ["2020-01-10"]})
    with pytest.raises(ValueError, match="Unknown variable"):
        link_climate_dataframe(df, variables=["temperatur"], fetch_fn=make_fetcher())


def test_window_shorter_than_one_rejected():
    df = pd.DataFrame({"latitude": [-26.2], "longitude": [28.0], "date": ["2020-01-10"]})
    with pytest.raises(ValueError, match="windows must be"):
        link_climate_dataframe(df, windows=[0], fetch_fn=make_fetcher())
