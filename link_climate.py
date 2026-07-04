#!/usr/bin/env python3
"""
Link biological / point observations to climate exposure windows.

Take a CSV where **each row has its own location and its own date** (a biological
sample, a clinical visit, a survey point) and write out the same rows enriched
with climate aggregates over the days leading up to each observation.

Examples
--------
Basic (temperature, default windows of 1, 7 and 30 days):

    python link_climate.py --input samples.csv --output samples_climate.csv \
        --lat-col latitude --lon-col longitude --date-col date

Multiple variables and custom windows, plus a 3-day lag (exclude the 3 days
immediately before the event):

    python link_climate.py -i samples.csv -o out.csv \
        --variables temperature,precipitation,humidity \
        --windows 7,14,30,60 --lag 3

The input CSV needs latitude, longitude and date columns (names configurable).
Everything else in the file is carried through untouched.
"""

import argparse
import sys

import pandas as pd

# Allow running from anywhere: make the repo root importable.
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.bio_climate_link import link_climate_dataframe, VARIABLE_COLUMNS  # noqa: E402


def _parse_int_list(text: str) -> list:
    return [int(x) for x in str(text).replace(" ", "").split(",") if x != ""]


def _parse_str_list(text: str) -> list:
    return [x for x in str(text).replace(" ", "").split(",") if x != ""]


def main():
    parser = argparse.ArgumentParser(
        description="Link biological observations (location + timestamp) to climate exposure windows.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-i", "--input", required=True, help="Input CSV path")
    parser.add_argument("-o", "--output", required=True, help="Output CSV path")
    parser.add_argument("--lat-col", default="latitude", help="Latitude column name")
    parser.add_argument("--lon-col", default="longitude", help="Longitude column name")
    parser.add_argument("--date-col", default="date", help="Observation date column (YYYY-MM-DD)")
    parser.add_argument("--id-col", default=None, help="Optional identifier column (carried through)")
    parser.add_argument(
        "--variables", default="temperature",
        help=f"Comma-separated climate variables. Options: {','.join(sorted(VARIABLE_COLUMNS))}",
    )
    parser.add_argument(
        "--windows", default="1,7,30",
        help="Comma-separated window lengths in days (each = N days ending on the observation date)",
    )
    parser.add_argument(
        "--lag", type=int, default=0,
        help="Days to shift each window back before the observation date",
    )
    parser.add_argument(
        "--buffer-km", type=float, default=0.0,
        help="Spatial buffer radius in km (0 = exact point)",
    )
    parser.add_argument(
        "--coord-decimals", type=int, default=3,
        help="Round coordinates to this many decimals when grouping sites (3 ~ 100 m)",
    )
    parser.add_argument("--project-id", default=None, help="Google Earth Engine / Cloud project id")
    parser.add_argument("--no-same-day", action="store_true", help="Do not emit same-day raw values")
    parser.add_argument("--no-coverage", action="store_true", help="Do not emit data-coverage columns")

    args = parser.parse_args()

    try:
        df = pd.read_csv(args.input)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Could not read input CSV '{args.input}': {exc}")
        sys.exit(1)

    print(f"📄 Read {len(df)} rows from {args.input}")
    print("🔗 Linking climate exposure windows — this queries Google Earth Engine per site...")

    try:
        enriched = link_climate_dataframe(
            df,
            lat_col=args.lat_col,
            lon_col=args.lon_col,
            date_col=args.date_col,
            id_col=args.id_col,
            variables=_parse_str_list(args.variables),
            windows=_parse_int_list(args.windows),
            lag=args.lag,
            buffer_km=args.buffer_km,
            coord_decimals=args.coord_decimals,
            include_same_day=not args.no_same_day,
            add_coverage=not args.no_coverage,
            project_id=args.project_id,
            progress=True,
        )
    except (KeyError, ValueError, RuntimeError) as exc:
        print(f"❌ {exc}")
        sys.exit(1)

    enriched.to_csv(args.output, index=False)
    new_cols = [c for c in enriched.columns if c not in df.columns]
    print(f"✅ Wrote {len(enriched)} rows and {len(new_cols)} new climate columns to {args.output}")
    print(f"   New columns: {', '.join(new_cols)}")


if __name__ == "__main__":
    main()
