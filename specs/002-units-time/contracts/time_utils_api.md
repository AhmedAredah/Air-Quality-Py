# Contracts — Time Utilities API (Feature 002)

Status: Phase 1 — Contracts
Date: 2025-11-08

Contracts specify behavior and error modes; no implementation code here.

## Functions

### ensure_timezone_aware

- Signature: `datetime ensure_timezone_aware(dt: datetime)`
- Behavior: If naive, attach UTC tzinfo; if aware, return as-is.
- Errors: `TypeError` if input is not datetime-like.

### to_utc

- Signature: `datetime to_utc(dt: datetime)`
- Behavior: Converts aware datetimes to UTC (preserving instant); naive treated as UTC.
- Errors: `TypeError` if input is not datetime-like.

### compute_time_bounds

- Signature: `TimeBounds compute_time_bounds(lazyframe: pl.LazyFrame, time_col: str = "datetime")`
- Behavior: Uses Polars min/max aggregation, single collect, returns tz-aware UTC bounds preserving full precision.
- Errors: Underlying schema or column errors surfaced (KeyError/Polars error); do not mask.

### resample_mean

- Signature: `pd.DataFrame resample_mean(df: pd.DataFrame, rule: str = "1H", time_col: str = "datetime")`
- Behavior: Uses pandas resample on datetime index/column; returns mean of numeric columns; input is not mutated.
- Errors: Raises if datetime coercion fails; type errors surfaced; do not mutate original df.

### rolling_window_mean

- Signature: `pd.DataFrame rolling_window_mean(df: pd.DataFrame, window: int = 3, time_col: str = "datetime")`
- Behavior: Centered rolling mean with min_periods=1; sorts by time first; numeric columns only; returns new df.
- Errors: ValueError if window < 1; datetime parse errors surfaced.

## Non-Functional

- Vectorized operations only; no row-wise loops (Sec 11).
- Immutability of inputs (Sec 10, 15).

---
End of time utilities contracts
