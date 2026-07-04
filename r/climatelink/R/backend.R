#' Configure the climatelink backend
#'
#' Tell climatelink where the cloned Climate_API repository lives and, optionally,
#' which Python interpreter to use. Settings are stored as options for the session.
#'
#' @param repo Path to the cloned Climate_API repository (the folder containing
#'   `src/bio_climate_link.py`). If `NULL`, climatelink tries to auto-detect it.
#' @param python Optional path to a Python interpreter that has `earthengine-api`,
#'   `geemap`, `pandas` and `numpy` installed. Must be set before the first call
#'   that touches Python.
#' @return Invisibly, a list of the resolved settings.
#' @export
climate_config <- function(repo = NULL, python = NULL) {
  if (!is.null(repo)) {
    repo <- normalizePath(repo, mustWork = TRUE)
    if (!.is_repo(repo)) {
      stop("'", repo, "' does not contain src/bio_climate_link.py", call. = FALSE)
    }
    options(climatelink.repo = repo)
    # Force a re-import next time so a new repo takes effect.
    .climate_state$module <- NULL
  }
  if (!is.null(python)) {
    options(climatelink.python = python)
    reticulate::use_python(python, required = TRUE)
    .climate_state$module <- NULL
  }
  invisible(list(
    repo = getOption("climatelink.repo", ""),
    python = getOption("climatelink.python", "")
  ))
}

#' Report the status of the Python backend
#'
#' Prints the resolved repository, Python interpreter, and whether the required
#' Python packages are importable. Useful for a one-line health check.
#'
#' @return Invisibly, a list with the resolved settings and availability flags.
#' @export
climate_backend_status <- function() {
  repo <- tryCatch(.resolve_repo(), error = function(e) NA_character_)
  cfg <- tryCatch(reticulate::py_config(), error = function(e) NULL)
  pkgs <- c("pandas", "numpy", "ee", "geemap")
  avail <- vapply(
    pkgs,
    function(p) tryCatch(reticulate::py_module_available(p), error = function(e) FALSE),
    logical(1)
  )
  cat("climatelink backend status\n")
  cat("  repo:   ", if (is.na(repo)) "NOT FOUND" else repo, "\n", sep = "")
  cat("  python: ", if (is.null(cfg)) "not initialised" else cfg$python, "\n", sep = "")
  for (p in pkgs) {
    cat(sprintf("  %-8s %s\n", paste0(p, ":"), if (avail[[p]]) "ok" else "MISSING"))
  }
  invisible(list(repo = repo, python = if (is.null(cfg)) NA else cfg$python,
                 packages = avail))
}

#' Install the Python packages the backend needs
#'
#' Convenience wrapper around [reticulate::py_install()] to install the Earth
#' Engine and data-science stack into the active reticulate environment. You only
#' need to run this once. After installing, authenticate with [ee_authenticate()].
#'
#' @param method,envname Passed through to [reticulate::py_install()].
#' @param ... Further arguments to [reticulate::py_install()].
#' @return Invisibly `NULL`.
#' @export
install_climate_backend <- function(method = "auto", envname = NULL, ...) {
  reticulate::py_install(
    packages = c("earthengine-api", "geemap", "pandas", "numpy", "requests"),
    method = method, envname = envname, ...
  )
  message("Backend packages installed. Next: ee_authenticate() then link_climate().")
  invisible(NULL)
}

#' Authenticate with Google Earth Engine
#'
#' Runs the Earth Engine authentication flow through the active Python. This
#' opens a browser to obtain credentials and only needs to be done once per
#' machine (credentials are cached by Earth Engine). If you have already run
#' `earthengine authenticate` in a terminal, you can skip this.
#'
#' @param project Optional Google Cloud project id to initialise with.
#' @return Invisibly `NULL`.
#' @export
ee_authenticate <- function(project = NULL) {
  ee <- reticulate::import("ee", convert = TRUE)
  ee$Authenticate()
  if (!is.null(project)) {
    ee$Initialize(project = project)
  } else {
    ee$Initialize()
  }
  message("Earth Engine authenticated and initialised.")
  invisible(NULL)
}
