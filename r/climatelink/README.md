# climatelink

**Link biological data (a location + a timestamp per row) to climate exposure windows — from R.**

`climatelink` gives R users a native `data.frame`-in / `data.frame`-out workflow
on top of the Python *Climate_API* toolkit and Google Earth Engine (ERA5-Land).
You bring a table of observations — each with a latitude, a longitude and a date —
and for every row it attaches climate summaries over the days leading up to that
observation (e.g. *mean temperature over the previous 30 days*, *total rainfall
over the previous 7 days*).

It queries Earth Engine **once per unique site**, then computes the windows
locally, so a dataset with many observations at a few field sites is fast and
cheap.

---

## How it works

`climatelink` is a thin [`reticulate`](https://rstudio.github.io/reticulate/)
wrapper: your R data frame is handed to the Python extractor in the cloned
`Climate_API` repo, which pulls ERA5-Land daily climate from Earth Engine and
returns the enriched table straight back to R. You never write any Python.

```
R data.frame ──► climatelink::link_climate() ──► reticulate ──► Python (Climate_API)
                                                                     │
                                                        Google Earth Engine (ERA5-Land)
                                                                     │
enriched R data.frame ◄──────────────────────────────────────────── ┘
```

## One-time setup

This runs Earth Engine through Python under the hood, so setup is a one-time,
three-part job. Budget ~15 minutes the first time. After that, every analysis is
pure R.

### Step 1 — Get a (free) Google Earth Engine project

1. Sign up at <https://earthengine.google.com> (free for research/non-commercial;
   approval is usually quick).
2. Open <https://code.earthengine.google.com>. The **project id** shown top-right
   (something like `ee-yourname`) is what you pass as `project_id = "..."` later.
   Note it down.

### Step 2 — Install this R package

```r
install.packages(c("reticulate", "remotes"))
remotes::install_local("r/climatelink")   # path to this folder in the cloned repo
library(climatelink)
```

### Step 3 — Connect a Python backend

`climatelink` needs a Python that has `earthengine-api`, `geemap`, `pandas` and
`numpy`. Pick the path that matches you:

**Path A — you already have Python/conda** (common if you use Anaconda). Point
climatelink at it, installing the packages there if needed:

```r
climate_config(python = "/opt/anaconda3/bin/python3")   # <- your python path
# In a terminal (once):  pip install earthengine-api geemap pandas numpy
```
(Find your path in a terminal with `which python3`, or in R with
`Sys.which("python3")`.)

**Path B — you don't have Python and don't want to think about it.** Let R build
an isolated environment and install everything for you:

```r
reticulate::install_python()   # only if you have no Python at all
install_climate_backend()      # installs earthengine-api, geemap, pandas, numpy
```

### Step 4 — Authenticate Earth Engine (once per machine)

```r
ee_authenticate(project = "ee-yourname")   # opens a browser to sign in
```
(If you have previously run `earthengine authenticate` in a terminal, you can
skip this — cached credentials are reused.)

### Step 5 — Tell climatelink where the repo is, and health-check

```r
climate_config(repo = "/path/to/Climate_API")   # the folder holding src/
climate_backend_status()                          # everything should say "ok"
```

`climate_backend_status()` should print `ok` for pandas, numpy, ee and geemap. If
`repo` shows `NOT FOUND`, set it with `climate_config(repo = ...)` as above (it is
auto-detected only when you run R from inside the repo).

## Connect your own data

Your table needs three things per row: a **latitude**, a **longitude** (decimal
degrees, WGS84 — the normal GPS numbers) and a **date**. Any other columns
(species, IDs, measurements) are carried straight through.

```r
library(climatelink)

# 1. Read your data (any column names are fine — you name them below).
mydata <- read.csv("my_field_samples.csv")

# 2. Link climate. Tell it which columns hold lat / lon / date.
linked <- link_climate(
  mydata,
  lat_col   = "latitude",     # <- your longitude/latitude/date column names
  lon_col   = "longitude",
  date_col  = "date",
  variables = c("temperature", "precipitation"),
  windows   = c(7, 30),       # prior 7 and 30 days
  buffer_km = 10,             # recommended; robust near coasts/water
  project_id = "ee-yourname"  # your Earth Engine project id
)

# 3. Save the enriched table.
write.csv(linked, "my_field_samples_with_climate.csv", row.names = FALSE)
```

That's the whole workflow. Everything below is detail on the options and outputs.

## Usage (worked example)

```r
library(climatelink)

obs <- data.frame(
  sample_id = c("bird_01", "bird_02", "bird_03"),
  latitude  = c(-26.2678, -26.2678, -33.9249),
  longitude = c( 27.8607,  27.8607,  18.4241),
  date      = as.Date(c("2021-01-15", "2021-06-20", "2021-03-10"))
)

linked <- link_climate(
  obs,
  variables = c("temperature", "precipitation"),
  windows   = c(7, 14, 30),   # summarise the prior 7 / 14 / 30 days
  buffer_km = 10,             # robust for coastal / water-adjacent sites
  project_id = "your-gee-project"
)

linked[, c("sample_id", "date",
           "tmean_celsius_mean_30d", "tmax_celsius_max_30d",
           "precipitation_mm_sum_30d", "coverage_30d")]
```

### Output columns

For each requested window `N` and variable you get columns named
`{variable}_{aggregation}_{N}d`:

| Column | Meaning |
|---|---|
| `tmean_celsius_mean_30d` | Mean daily mean-temperature over the 30 days ending on the observation date |
| `tmax_celsius_max_7d`    | Hottest daily max over the prior 7 days |
| `precipitation_mm_sum_30d` | Total rainfall over the prior 30 days |
| `tmean_celsius` | Same-day mean temperature (raw value on the observation date) |
| `coverage_30d` | Fraction of the 30-day window that had data (**check this is 1.0**) |
| `*_n` | Number of days with data behind each aggregate |

### Key arguments

| Argument | Default | What it does |
|---|---|---|
| `variables` | `"temperature"` | Any of `temperature`, `precipitation`, `humidity`, `wind`, `solar`, `pressure`, `evapotranspiration` |
| `windows` | `c(1, 7, 30)` | Window lengths in days (each ends on the observation date) |
| `lag` | `0` | Shift every window back by this many days (e.g. exclude the event day) |
| `buffer_km` | `0` | `0` = exact pixel; `>0` averages land pixels in the buffer (use for coastal sites) |
| `aggregations` | `NULL` | Override defaults, e.g. `list(tmean_celsius = c("mean", "max"))` |

## Watch out for

- **`coverage_*` below 1.0** means the window had missing days. The most common
  cause is a site on a coastal / water pixel that ERA5-Land masks — set
  `buffer_km = 10` (or more) so land pixels are averaged in.
- **Dates**: `Date`, `POSIXct`, or `"YYYY-MM-DD"` strings all work.
- ERA5-Land starts in 1950; daily aggregates are the native resolution here.

## Function reference

- `link_climate()` — the main data.frame → data.frame linkage.
- `link_climate_csv()` — file-in / file-out convenience wrapper.
- `climate_config()` — set the repo path and/or Python interpreter.
- `climate_backend_status()` — one-line health check.
- `install_climate_backend()` — install the Python stack via reticulate.
- `ee_authenticate()` — run the Earth Engine auth flow from R.
