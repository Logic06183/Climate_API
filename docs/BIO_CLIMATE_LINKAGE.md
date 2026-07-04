# Linking Biological Data to Climate

This guide covers the **linkage** workflow: taking observations that each carry a
**location and a timestamp** and attaching the climate they experienced, over
configurable exposure windows. It works from **R**, **Python**, and the
**command line** — all three call the same engine.

- Python core: [`src/bio_climate_link.py`](../src/bio_climate_link.py)
- Command line: [`link_climate.py`](../link_climate.py)
- R package: [`r/climatelink`](../r/climatelink/README.md)
- Example data: [`examples/bio_samples_example.csv`](../examples/bio_samples_example.csv)

---

## The idea

An organism (or patient, or site) experiences weather over a *period*, not on a
single instant. So for each observation at `(latitude, longitude, date)` we
summarise a daily climate series over a **window** of `N` days ending on the
observation date:

```
        window = 30 days
   |<---------------------------->|
   ..............................●      ● = observation date
   day-29                      day-0
        mean / max / min / sum
```

You choose the variables, the window lengths, and (optionally) a lag that shifts
the window earlier. The result is your original table with new climate columns
appended — ready to drop into a model.

### Output column naming

| Pattern | Example | Meaning |
|---|---|---|
| `{var}_{agg}_{N}d` | `tmean_celsius_mean_30d` | Aggregate of a variable over the N-day window |
| `{var}` | `tmean_celsius` | Same-day raw value on the observation date |
| `{var}_{agg}_{N}d_n` | `precipitation_mm_sum_7d_n` | Number of days with data behind that aggregate |
| `coverage_{N}d` | `coverage_30d` | Fraction of the window's days that had data (**should be 1.0**) |

### Variables and default aggregations

| Variable | Raw columns | Default aggregations |
|---|---|---|
| `temperature` | `tmax_celsius`, `tmean_celsius` | mean, max (and min for mean-temp) |
| `precipitation` | `precipitation_mm` | sum, mean |
| `humidity` | `dewpoint_celsius` | mean |
| `wind` | `wind_speed_ms`, `wind_u_ms`, `wind_v_ms` | mean, max |
| `solar` | `solar_radiation_jm2` | mean |
| `pressure` | `surface_pressure_pa` | mean |
| `evapotranspiration` | `evapotranspiration_mm` | sum, mean |

Data source: **ERA5-Land daily aggregates** (`ECMWF/ERA5_LAND/DAILY_AGGR`) via
Google Earth Engine. Available from 1950 to ~5 days ago.

---

## R

See [`r/climatelink/README.md`](../r/climatelink/README.md) for full setup. In short:

```r
library(climatelink)
climate_config(python = "/path/to/python")   # a Python with earthengine-api + geemap
# ee_authenticate(project = "your-gee-project")   # once per machine

obs <- data.frame(
  sample_id = c("S001", "S002"),
  latitude  = c(-26.2678, -33.9249),
  longitude = c( 27.8607,  18.4241),
  date      = as.Date(c("2021-01-15", "2021-03-10"))
)

linked <- link_climate(
  obs,
  variables  = c("temperature", "precipitation"),
  windows    = c(7, 14, 30),
  buffer_km  = 10,
  project_id = "your-gee-project"
)
```

## Command line

```bash
python link_climate.py \
  --input examples/bio_samples_example.csv \
  --output examples/bio_samples_linked.csv \
  --variables temperature,precipitation \
  --windows 7,30 \
  --buffer-km 10 \
  --project-id your-gee-project
```

Column names for latitude / longitude / date are configurable
(`--lat-col`, `--lon-col`, `--date-col`). Run `python link_climate.py --help`.

## Python

```python
import pandas as pd
from src.bio_climate_link import link_climate_dataframe

df = pd.read_csv("examples/bio_samples_example.csv")
linked = link_climate_dataframe(
    df,
    lat_col="latitude", lon_col="longitude", date_col="date",
    variables=["temperature", "precipitation"],
    windows=[7, 14, 30],
    lag=0,
    buffer_km=10,
    project_id="your-gee-project",
)
linked.to_csv("linked.csv", index=False)
```

---

## Key options

| Option (Py / CLI / R) | Default | Notes |
|---|---|---|
| `windows` / `--windows` | `1,7,30` | Window lengths in days, each ending on the observation date |
| `lag` / `--lag` | `0` | Shift every window back by this many days |
| `buffer_km` / `--buffer-km` | `0` | `0` = exact pixel; `>0` averages land pixels in the buffer |
| `aggregations` | per-variable defaults | Override, e.g. `{"tmean_celsius": ["mean", "max"]}` |
| `coord_decimals` / `--coord-decimals` | `3` | Rounding used to group observations into unique sites (≈100 m) |
| `include_same_day` / `--no-same-day` | on | Emit the raw same-day value of each variable |
| `add_coverage` / `--no-coverage` | on | Emit `coverage_Nd` and `_n` data-quality columns |

## Performance model

Earth Engine is queried **once per unique site** (coordinates rounded to
`coord_decimals`), over that site's full date span padded by the longest window.
So cost scales with the number of *distinct locations*, not the number of rows.
500 samples from 10 field sites → 10 Earth Engine calls.

## Data-quality gotchas

- **`coverage_Nd < 1.0`** — the window had missing days. The usual culprit is a
  point on a coastal / water pixel that ERA5-Land masks as nodata. Fix it with
  `buffer_km = 10` (or larger), which averages the surrounding **land** pixels.
  This is why the Cape Town example returns `NA` at `buffer_km = 0` but resolves
  with a buffer.
- **Unparseable dates** produce all-`NA` climate for that row (and a warning).
- **Future / pre-1950 dates** fall outside ERA5-Land and return `NA`.

## How it fits the rest of the toolkit

The linkage reuses the existing `ClimateDataExtractor` in
[`src/climate_utils.py`](../src/climate_utils.py) — the same extractor behind the
CLI and web app. The one core enhancement it required was a `spatial_reducer`
option on `extract_climate_data()` (`'point'` vs `'mean'`) so buffered,
water-robust sampling is possible; the default remains exact-point and fully
backward-compatible.
