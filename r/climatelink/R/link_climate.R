#' Link biological observations to climate exposure windows
#'
#' For each row of `data` (which must carry a latitude, a longitude and a date),
#' attach climate aggregates over the days leading up to the observation. Earth
#' Engine is queried once per unique site, then windows are computed locally, so
#' repeated field sites are cheap.
#'
#' Output columns are named `{variable}_{aggregation}_{N}d` — for example
#' `tmean_celsius_mean_30d` is the mean daily mean-temperature over the 30 days
#' ending on the observation date. Same-day raw values are named `{variable}`
#' (e.g. `tmean_celsius`). A `coverage_{N}d` column reports the fraction of each
#' window's days that had data (watch for values < 1, which flag gaps or masked
#' pixels).
#'
#' @param data A data.frame of observations.
#' @param lat_col,lon_col Names of the latitude / longitude columns (decimal
#'   degrees, WGS84).
#' @param date_col Name of the observation-date column. Dates, POSIXct or
#'   "YYYY-MM-DD" character are all accepted.
#' @param id_col Optional identifier column name (carried through untouched).
#' @param variables Character vector of climate variables to link. One or more of
#'   `"temperature"`, `"precipitation"`, `"humidity"`, `"wind"`, `"solar"`,
#'   `"pressure"`, `"evapotranspiration"`.
#' @param windows Integer vector of window lengths in days. A window of `N` covers
#'   the `N` days ending on (and including) the observation date.
#' @param lag Days to shift every window back before the observation date
#'   (e.g. `lag = 1` ends each window the day before the event).
#' @param buffer_km Spatial buffer radius in km. `0` samples the exact pixel;
#'   a positive value averages over land pixels within the buffer, which is the
#'   robust choice for coastal or water-adjacent sites where the exact pixel may
#'   be masked (returns `NA`).
#' @param aggregations Optional named list overriding the default aggregation(s)
#'   per raw column, e.g. `list(tmean_celsius = c("mean", "max"))`.
#' @param include_same_day If `TRUE`, also return the raw same-day value of each
#'   variable.
#' @param add_coverage If `TRUE`, add data-coverage columns.
#' @param coord_decimals Decimals to round coordinates to when grouping sites
#'   (3 is roughly 100 m).
#' @param project_id Google Earth Engine / Cloud project id to initialise with.
#' @param progress If `TRUE`, print per-site progress.
#'
#' @return A data.frame: `data` with the climate columns appended (original row
#'   order preserved).
#'
#' @examples
#' \dontrun{
#' obs <- data.frame(
#'   id = c("a", "b"),
#'   latitude = c(-26.2678, -33.9249),
#'   longitude = c(27.8607, 18.4241),
#'   date = as.Date(c("2021-01-15", "2021-03-10"))
#' )
#' linked <- link_climate(
#'   obs,
#'   variables = c("temperature", "precipitation"),
#'   windows = c(1, 7, 30),
#'   buffer_km = 10,          # robust for the coastal Cape Town point
#'   project_id = "your-gee-project"
#' )
#' }
#' @export
link_climate <- function(data,
                         lat_col = "latitude",
                         lon_col = "longitude",
                         date_col = "date",
                         id_col = NULL,
                         variables = "temperature",
                         windows = c(1, 7, 30),
                         lag = 0,
                         buffer_km = 0,
                         aggregations = NULL,
                         include_same_day = TRUE,
                         add_coverage = TRUE,
                         coord_decimals = 3,
                         project_id = NULL,
                         progress = TRUE) {
  if (!is.data.frame(data)) stop("'data' must be a data.frame", call. = FALSE)
  for (col in c(lat_col, lon_col, date_col)) {
    if (!col %in% names(data)) {
      stop("Column '", col, "' not found in 'data'. Available: ",
           paste(names(data), collapse = ", "), call. = FALSE)
    }
  }

  # Normalise dates to "YYYY-MM-DD" character so reticulate ships them cleanly to
  # pandas (Date/POSIXct can otherwise arrive as numbers).
  data <- as.data.frame(data)
  if (inherits(data[[date_col]], c("Date", "POSIXct", "POSIXt"))) {
    data[[date_col]] <- format(as.Date(data[[date_col]]), "%Y-%m-%d")
  } else {
    data[[date_col]] <- as.character(data[[date_col]])
  }

  mod <- .get_module()

  py_aggs <- if (is.null(aggregations)) NULL else lapply(aggregations, as.list)

  result <- mod$link_climate_dataframe(
    df = reticulate::r_to_py(data),
    lat_col = lat_col,
    lon_col = lon_col,
    date_col = date_col,
    id_col = id_col,
    variables = as.list(as.character(variables)),
    windows = as.list(as.integer(windows)),
    lag = as.integer(lag),
    aggregations = py_aggs,
    include_same_day = isTRUE(include_same_day),
    add_coverage = isTRUE(add_coverage),
    buffer_km = as.numeric(buffer_km),
    coord_decimals = as.integer(coord_decimals),
    project_id = project_id,
    progress = isTRUE(progress)
  )

  out <- reticulate::py_to_r(result)
  rownames(out) <- NULL
  out
}

#' Link a CSV of observations to climate exposure windows
#'
#' File-in / file-out convenience wrapper around [link_climate()]. Reads
#' `input_path`, links it, and writes the enriched table to `output_path`.
#'
#' @param input_path,output_path Input and output CSV paths.
#' @param ... Passed to [link_climate()].
#' @return Invisibly, the enriched data.frame.
#' @export
link_climate_csv <- function(input_path, output_path, ...) {
  data <- utils::read.csv(input_path, stringsAsFactors = FALSE)
  linked <- link_climate(data, ...)
  utils::write.csv(linked, output_path, row.names = FALSE)
  message("Wrote ", nrow(linked), " rows to ", output_path)
  invisible(linked)
}
