# Quickstart — Feature 002: Units & Time Primitives

Status: Phase 1 — Draft
Date: 2025-11-08

This is a usage sketch for the planned API. It is illustrative; no code is implemented yet.

## Units

Example flow for converting and rounding values:

1. Parse or validate units and convert:
   - `Unit.parse("ug/m3")` → `Unit.UG_M3`
   - `convert_values(series, Unit.UG_M3, Unit.MG_M3)`

2. Apply standardized rounding for reporting (per-unit defaults, optional pollutant override):
   - `round_for_reporting(series, Unit.MG_M3, pollutant="NO2")`

3. Normalize dataset unit metadata:
   - `validate_units_schema({"conc":"ug/m3", "unc": Unit.UG_M3})` → `{ "conc": Unit.UG_M3, "unc": Unit.UG_M3 }`

## Time utilities

1. Compute bounds (Polars LazyFrame):
   - `compute_time_bounds(lf, time_col="datetime")` → `TimeBounds(start=..., end=...)` (tz-aware UTC, sub-second preserved)

2. Resample hourly mean (pandas):
   - `resample_mean(df, rule="1H", time_col="datetime")` → new DataFrame; original `df` unchanged

3. Rolling mean QC helper:
   - `rolling_window_mean(df, window=3, time_col="datetime")`

## Notes

- All operations are vectorized; no row-wise loops.
- Time bounds perform a single `.collect()`; resampling relies on pandas at the boundary.

---
End of quickstart draft
