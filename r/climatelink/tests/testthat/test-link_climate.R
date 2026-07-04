# These tests exercise the R-side argument handling that runs *before* any Python
# / Earth Engine call, so they need no network or GEE credentials.

test_that("link_climate rejects a non-data.frame", {
  expect_error(link_climate(list(a = 1)), "must be a data.frame")
})

test_that("link_climate errors on a missing coordinate column", {
  df <- data.frame(lon = 1, date = "2021-01-01")  # no latitude/longitude
  expect_error(
    link_climate(df, lat_col = "latitude", lon_col = "longitude"),
    "Column 'latitude' not found"
  )
})

test_that("climate_config validates the repo path", {
  expect_error(
    climate_config(repo = tempdir()),
    "does not contain src/bio_climate_link.py"
  )
})

test_that("repo auto-detection finds this repository from the package tree", {
  # The package lives under <repo>/r/climatelink, so walking up must find the repo.
  repo <- tryCatch(climatelink:::.resolve_repo(), error = function(e) NA_character_)
  skip_if(is.na(repo), "repo not locatable in this environment")
  expect_true(file.exists(file.path(repo, "src", "bio_climate_link.py")))
})
