"""
Link biological / point observations to climate data.

This module solves the problem the rest of the toolkit does *not*: taking a table
of observations where **each row has its own location AND its own timestamp**
(e.g. a biological sample, a clinical visit, a trap catch) and attaching climate
variables to every row, using **exposure windows** — aggregates (mean / max / min /
sum) over the N days leading up to each observation's date.

Design notes
------------
* The GEE fetch (slow, needs auth/network) is cleanly separated from the window
  aggregation (pure pandas). ``compute_exposure_windows`` is deterministic and
  fully unit-testable offline; ``link_climate_dataframe`` wires the fetch in.
* Observations are grouped by unique location so we hit Earth Engine **once per
  site** over the union of that site's date span (+ the longest window), instead
  of once per row. For biological datasets with repeated sites this is a large
  speed-up.
* Aggregations default to something sensible per variable (precipitation is
  summed, temperature is mean/max, etc.) but are fully overridable.

The public entry points are :func:`link_climate_dataframe` (DataFrame in, enriched
DataFrame out) and :func:`link_climate_csv` (file in, file out).
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration / defaults
# ---------------------------------------------------------------------------

# Which raw climate columns each variable category produces (mirrors
# ClimateDataExtractor.extract_climate_data in climate_utils.py).
VARIABLE_COLUMNS: Dict[str, List[str]] = {
    "temperature": ["tmax_celsius", "tmean_celsius"],
    "precipitation": ["precipitation_mm"],
    "humidity": ["dewpoint_celsius"],
    "wind": ["wind_speed_ms", "wind_u_ms", "wind_v_ms"],
    "solar": ["solar_radiation_jm2"],
    "pressure": ["surface_pressure_pa"],
    "evapotranspiration": ["evapotranspiration_mm"],
}

# Sensible default aggregation(s) for each raw climate column. Fluxes that
# accumulate over a day (rain, ET) are summed; states are averaged.
DEFAULT_AGGREGATIONS: Dict[str, List[str]] = {
    "tmax_celsius": ["mean", "max"],
    "tmean_celsius": ["mean", "min", "max"],
    "precipitation_mm": ["sum", "mean"],
    "dewpoint_celsius": ["mean"],
    "wind_speed_ms": ["mean", "max"],
    "wind_u_ms": ["mean"],
    "wind_v_ms": ["mean"],
    "solar_radiation_jm2": ["mean"],
    "surface_pressure_pa": ["mean"],
    "evapotranspiration_mm": ["sum", "mean"],
}

_FALLBACK_AGG = ["mean"]

# Aggregation name -> numpy reducer. All ignore NaN so partial coverage still
# yields a value (coverage is reported separately).
_AGG_FUNCS: Dict[str, Callable[[np.ndarray], float]] = {
    "mean": np.nanmean,
    "max": np.nanmax,
    "min": np.nanmin,
    "sum": np.nansum,
    "median": np.nanmedian,
    "std": np.nanstd,
}


# ---------------------------------------------------------------------------
# Pure aggregation logic (no Earth Engine — unit-testable offline)
# ---------------------------------------------------------------------------

def _resolve_aggregations(
    value_cols: Sequence[str],
    aggregations: Optional[Dict[str, Sequence[str]]],
) -> Dict[str, List[str]]:
    """Return {column: [agg, ...]} for every value column.

    ``aggregations`` may map a column name to a list of aggregation names to
    override the defaults; unspecified columns fall back to DEFAULT_AGGREGATIONS.
    """
    resolved: Dict[str, List[str]] = {}
    overrides = aggregations or {}
    for col in value_cols:
        if col in overrides:
            aggs = list(overrides[col])
        else:
            aggs = DEFAULT_AGGREGATIONS.get(col, _FALLBACK_AGG)
        for agg in aggs:
            if agg not in _AGG_FUNCS:
                raise ValueError(
                    f"Unknown aggregation '{agg}' for column '{col}'. "
                    f"Valid options: {sorted(_AGG_FUNCS)}"
                )
        resolved[col] = aggs
    return resolved


def compute_exposure_windows(
    observations: pd.DataFrame,
    climate: pd.DataFrame,
    date_col: str,
    value_cols: Sequence[str],
    windows: Sequence[int],
    lag: int = 0,
    aggregations: Optional[Dict[str, Sequence[str]]] = None,
    include_same_day: bool = True,
    add_coverage: bool = True,
) -> pd.DataFrame:
    """Attach exposure-window climate summaries to a set of observations.

    This is the deterministic core of the linkage. It performs **no** Earth
    Engine calls, which makes it trivially unit-testable with a synthetic
    ``climate`` series.

    Parameters
    ----------
    observations
        Rows to enrich. Must contain ``date_col``. All rows are assumed to share
        the single daily ``climate`` series passed in (i.e. same location).
    climate
        Daily climate for this location: a ``date`` column plus ``value_cols``.
    date_col
        Name of the observation date column (parseable to datetime).
    value_cols
        Climate columns to summarise.
    windows
        Window lengths in days. A window of ``N`` covers the ``N`` days ending on
        (and including) the observation date, i.e. ``[date-(N-1), date]``. Use
        ``lag`` to shift the whole window earlier.
    lag
        Days to shift each window back before the observation date. ``lag=0``
        (default) means the window ends on the observation date; ``lag=1`` means
        it ends the day before, etc.
    aggregations
        Optional ``{column: [agg, ...]}`` overrides. See DEFAULT_AGGREGATIONS.
    include_same_day
        If True, also emit the raw same-day value of each column as ``{col}``.
    add_coverage
        If True, emit ``{col}_{agg}_{N}d_n`` = number of days with data and a
        single ``coverage_{N}d`` = fraction of the window's days that had data.

    Returns
    -------
    pd.DataFrame
        ``observations`` (index preserved) with the new climate columns appended.
    """
    resolved = _resolve_aggregations(value_cols, aggregations)

    clim = climate.copy()
    clim[date_col] = pd.to_datetime(clim["date"])
    clim = clim.dropna(subset=[date_col]).sort_values(date_col)
    # Index by normalised (midnight) date so .loc slicing is by calendar day.
    clim = clim.set_index(clim[date_col].dt.normalize())

    obs = observations.copy()
    obs_dates = pd.to_datetime(obs[date_col]).dt.normalize()

    # Pre-allocate output columns so dtype is float and order is stable.
    out: Dict[str, list] = {}
    for w in windows:
        for col in value_cols:
            for agg in resolved[col]:
                out[_window_col_name(col, agg, w)] = []
                if add_coverage:
                    out[f"{_window_col_name(col, agg, w)}_n"] = []
        if add_coverage:
            out[f"coverage_{w}d"] = []
    if include_same_day:
        for col in value_cols:
            out[col] = []

    date_index = clim.index
    for obs_date in obs_dates:
        if pd.isna(obs_date):
            # No date -> everything NaN for this row.
            for key in out:
                out[key].append(np.nan)
            continue

        window_end = obs_date - pd.Timedelta(days=lag)
        for w in windows:
            window_start = window_end - pd.Timedelta(days=w - 1)
            mask = (date_index >= window_start) & (date_index <= window_end)
            block = clim.loc[mask]
            n_expected = w
            for col in value_cols:
                series = block[col] if col in block.columns else pd.Series(dtype=float)
                values = pd.to_numeric(series, errors="coerce").to_numpy()
                n_valid = int(np.count_nonzero(~np.isnan(values)))
                for agg in resolved[col]:
                    name = _window_col_name(col, agg, w)
                    out[name].append(_reduce(values, agg))
                    if add_coverage:
                        out[f"{name}_n"].append(n_valid)
            if add_coverage:
                out[f"coverage_{w}d"].append(
                    _coverage(block, value_cols, n_expected)
                )

        if include_same_day:
            same = clim.loc[clim.index == window_end] if lag == 0 else \
                clim.loc[clim.index == obs_date]
            for col in value_cols:
                if col in same.columns and len(same):
                    val = pd.to_numeric(same[col], errors="coerce")
                    out[col].append(float(val.iloc[0]) if len(val) else np.nan)
                else:
                    out[col].append(np.nan)

    # Keep the observations' original index so callers can re-order groups back
    # into the input order. Lists in ``out`` are positional (built in obs order),
    # so assigning them aligns by position regardless of the index.
    result = obs.copy()
    for name, col_values in out.items():
        result[name] = col_values
    return result


def _window_col_name(col: str, agg: str, window: int) -> str:
    return f"{col}_{agg}_{window}d"


def _reduce(values: np.ndarray, agg: str) -> float:
    if values.size == 0 or np.all(np.isnan(values)):
        # nansum of an all-NaN slice is 0 in numpy, which is misleading here.
        return np.nan
    with np.errstate(all="ignore"):
        return float(_AGG_FUNCS[agg](values))


def _coverage(block: pd.DataFrame, value_cols: Sequence[str], n_expected: int) -> float:
    """Fraction of the window's expected days that carry any value."""
    if n_expected <= 0 or len(block) == 0:
        return 0.0 if n_expected > 0 else np.nan
    present = block[[c for c in value_cols if c in block.columns]]
    if present.shape[1] == 0:
        return 0.0
    days_with_data = present.notna().any(axis=1).sum()
    return round(float(days_with_data) / float(n_expected), 4)


# ---------------------------------------------------------------------------
# Earth Engine wiring
# ---------------------------------------------------------------------------

def _default_fetcher(project_id: Optional[str]) -> Callable:
    """Build a fetch function backed by ClimateDataExtractor.

    Returned callable signature: ``fetch(lat, lon, start, end, variables,
    buffer_km) -> pd.DataFrame`` with a ``date`` column plus value columns.
    """
    from src.climate_utils import ClimateDataExtractor  # local import: needs ee

    extractor = ClimateDataExtractor(project_id=project_id)
    if not extractor.initialized:
        raise RuntimeError(
            "Google Earth Engine could not be initialised. Run "
            "'earthengine authenticate' and check your project id."
        )

    def fetch(lat, lon, start, end, variables, buffer_km):
        geometry = extractor.create_study_area(lat=lat, lon=lon, buffer_km=buffer_km)
        point = extractor.create_point(lat, lon)
        # With a buffer, average over land pixels so masked (coastal/water)
        # pixels don't silently produce NaN; without one, sample the exact point.
        reducer = "mean" if buffer_km and buffer_km > 0 else "point"
        return extractor.extract_climate_data(
            geometry=geometry,
            point=point,
            start_date=start,
            end_date=end,
            variables=list(variables),
            spatial_reducer=reducer,
        )

    return fetch


def _round_key(value: float, decimals: int) -> float:
    return round(float(value), decimals)


def link_climate_dataframe(
    df: pd.DataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    date_col: str = "date",
    id_col: Optional[str] = None,
    variables: Optional[Sequence[str]] = None,
    windows: Sequence[int] = (1, 7, 30),
    lag: int = 0,
    aggregations: Optional[Dict[str, Sequence[str]]] = None,
    include_same_day: bool = True,
    add_coverage: bool = True,
    buffer_km: float = 0.0,
    coord_decimals: int = 3,
    project_id: Optional[str] = None,
    fetch_fn: Optional[Callable] = None,
    progress: bool = True,
) -> pd.DataFrame:
    """Link each row of ``df`` to climate exposure windows.

    Every row must carry a latitude, a longitude and a date. For each row we
    attach aggregates of the requested climate ``variables`` over the requested
    ``windows`` (days ending on the observation date, optionally shifted by
    ``lag``).

    Earth Engine is queried **once per unique location** (coordinates rounded to
    ``coord_decimals`` decimals ≈ 100 m) over that site's full date span plus the
    longest window, then windows are computed locally. Pass ``fetch_fn`` to inject
    a custom/offline data source (used by the test-suite); otherwise a
    ClimateDataExtractor-backed fetch is created automatically.

    Returns a copy of ``df`` with climate columns appended. Column names follow
    ``{variable}_{agg}_{N}d`` (e.g. ``tmean_celsius_mean_30d``); same-day raw
    values are ``{variable}`` (e.g. ``tmean_celsius``).
    """
    for col in (lat_col, lon_col, date_col):
        if col not in df.columns:
            raise KeyError(
                f"Column '{col}' not found. Available columns: {list(df.columns)}"
            )

    variables = list(variables) if variables else ["temperature"]
    unknown = [v for v in variables if v not in VARIABLE_COLUMNS]
    if unknown:
        raise ValueError(
            f"Unknown variable(s): {unknown}. Valid: {sorted(VARIABLE_COLUMNS)}"
        )
    value_cols: List[str] = []
    for v in variables:
        value_cols.extend(VARIABLE_COLUMNS[v])

    windows = [int(w) for w in windows]
    if any(w < 1 for w in windows):
        raise ValueError("windows must be >= 1 (a window of N days ending on the date)")
    max_window = max(windows)

    work = df.copy().reset_index(drop=True)
    work["_dt"] = pd.to_datetime(work[date_col], errors="coerce").dt.normalize()
    n_missing_date = int(work["_dt"].isna().sum())
    if n_missing_date and progress:
        print(f"⚠️  {n_missing_date} row(s) have an unparseable date; they will get NaN climate.")

    work["_latk"] = work[lat_col].astype(float).map(lambda x: _round_key(x, coord_decimals))
    work["_lonk"] = work[lon_col].astype(float).map(lambda x: _round_key(x, coord_decimals))

    if fetch_fn is None:
        fetch_fn = _default_fetcher(project_id)

    enriched_parts: List[pd.DataFrame] = []
    groups = work.groupby(["_latk", "_lonk"], sort=False)
    n_groups = groups.ngroups
    for i, ((latk, lonk), grp) in enumerate(groups, start=1):
        valid_dates = grp["_dt"].dropna()
        if valid_dates.empty:
            # No usable dates for this site; emit NaN climate columns.
            enriched_parts.append(
                compute_exposure_windows(
                    grp, _empty_climate(value_cols), "_dt", value_cols, windows,
                    lag=lag, aggregations=aggregations,
                    include_same_day=include_same_day, add_coverage=add_coverage,
                )
            )
            continue

        # Fetch the union span for this site, padded for the longest window + lag.
        start = (valid_dates.min() - pd.Timedelta(days=max_window + lag + 1)).strftime("%Y-%m-%d")
        # End date is exclusive in GEE filterDate; add a day to include the last obs.
        end = (valid_dates.max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

        if progress:
            print(f"🌍 [{i}/{n_groups}] site ({latk}, {lonk}) — {len(grp)} obs, "
                  f"{start} → {end}")

        try:
            climate = fetch_fn(latk, lonk, start, end, variables, buffer_km)
        except Exception as exc:  # noqa: BLE001 — surface per-site failures, keep going
            if progress:
                print(f"   ❌ fetch failed for ({latk}, {lonk}): {exc}")
            climate = _empty_climate(value_cols)

        if climate is None or climate.empty:
            climate = _empty_climate(value_cols)

        enriched_parts.append(
            compute_exposure_windows(
                grp, climate, "_dt", value_cols, windows,
                lag=lag, aggregations=aggregations,
                include_same_day=include_same_day, add_coverage=add_coverage,
            )
        )

    # ``work`` was reset to a 0..n-1 index, so sort_index restores input order.
    result = pd.concat(enriched_parts, axis=0).sort_index()
    result = result.drop(columns=["_dt", "_latk", "_lonk"], errors="ignore")
    result.index = df.index  # restore the caller's original index
    return result


def _empty_climate(value_cols: Sequence[str]) -> pd.DataFrame:
    cols = {"date": pd.Series([], dtype="datetime64[ns]")}
    for c in value_cols:
        cols[c] = pd.Series([], dtype=float)
    return pd.DataFrame(cols)


def link_climate_csv(
    input_path: str,
    output_path: str,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    date_col: str = "date",
    id_col: Optional[str] = None,
    variables: Optional[Sequence[str]] = None,
    windows: Sequence[int] = (1, 7, 30),
    **kwargs,
) -> pd.DataFrame:
    """Convenience wrapper: read a CSV, link it, write the enriched CSV out."""
    df = pd.read_csv(input_path)
    enriched = link_climate_dataframe(
        df,
        lat_col=lat_col,
        lon_col=lon_col,
        date_col=date_col,
        id_col=id_col,
        variables=variables,
        windows=windows,
        **kwargs,
    )
    enriched.to_csv(output_path, index=False)
    return enriched
