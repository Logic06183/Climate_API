# Package-level state and helpers for locating the Python backend.

# Cache for the imported Python module and resolved settings.
.climate_state <- new.env(parent = emptyenv())

`%||%` <- function(a, b) if (is.null(a) || identical(a, "") || length(a) == 0) b else a

.onLoad <- function(libname, pkgname) {
  # The Python backend prints progress with non-ASCII glyphs. Under R's (often
  # ASCII) stdout that raises UnicodeEncodeError, so make Python emit UTF-8. Must
  # be set before the interpreter starts, hence in .onLoad.
  if (identical(Sys.getenv("PYTHONIOENCODING"), "")) {
    Sys.setenv(PYTHONIOENCODING = "utf-8")
  }
  # Allow the Python interpreter to be chosen before reticulate initialises.
  py <- getOption("climatelink.python", Sys.getenv("CLIMATELINK_PYTHON", ""))
  if (!identical(py, "")) {
    try(reticulate::use_python(py, required = FALSE), silent = TRUE)
  }
}

# Find the cloned Climate_API repository (which holds src/bio_climate_link.py).
# Resolution order: explicit option -> env var -> walk up from a few sensible
# starting points looking for src/bio_climate_link.py.
.resolve_repo <- function() {
  cand <- getOption("climatelink.repo", Sys.getenv("CLIMATE_API_REPO", ""))
  if (!identical(cand, "") && .is_repo(cand)) {
    return(normalizePath(cand, mustWork = TRUE))
  }

  starts <- unique(c(
    getwd(),
    tryCatch(system.file(package = "climatelink"), error = function(e) "")
  ))
  starts <- starts[nzchar(starts)]

  for (start in starts) {
    hit <- .walk_up_for_repo(start)
    if (!is.null(hit)) return(hit)
  }

  stop(
    "Could not locate the Climate_API repository (the folder containing ",
    "src/bio_climate_link.py).\n",
    "Set it with:  climate_config(repo = \"/path/to/Climate_API\")\n",
    "or the environment variable CLIMATE_API_REPO.",
    call. = FALSE
  )
}

.is_repo <- function(path) {
  file.exists(file.path(path, "src", "bio_climate_link.py"))
}

.walk_up_for_repo <- function(start, max_depth = 8) {
  path <- normalizePath(start, mustWork = FALSE)
  for (i in seq_len(max_depth)) {
    if (.is_repo(path)) return(path)
    parent <- dirname(path)
    if (identical(parent, path)) break
    path <- parent
  }
  NULL
}

# Import (and cache) the Python linkage module, ensuring the repo root is on
# sys.path so `import src.bio_climate_link` resolves its internal imports.
.get_module <- function() {
  if (!is.null(.climate_state$module)) return(.climate_state$module)

  repo <- .resolve_repo()
  reticulate::py_run_string(sprintf(
    "import sys\n_p = r'%s'\nif _p not in sys.path:\n    sys.path.insert(0, _p)",
    repo
  ))
  # Belt and braces: if stdout still can't encode the backend's glyphs, degrade
  # gracefully instead of raising (older reticulate / exotic locales).
  reticulate::py_run_string(
    "import sys\ntry:\n    sys.stdout.reconfigure(errors='backslashreplace')\nexcept Exception:\n    pass"
  )

  if (!reticulate::py_module_available("pandas")) {
    stop(
      "The active Python has no 'pandas'. Point reticulate at a Python that has ",
      "pandas, numpy, earthengine-api and geemap (see install_climate_backend()).\n",
      "Current interpreter: ", reticulate::py_config()$python,
      call. = FALSE
    )
  }

  mod <- reticulate::import("src.bio_climate_link", convert = TRUE)
  .climate_state$module <- mod
  mod
}
