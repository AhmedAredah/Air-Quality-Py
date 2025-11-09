"""air_quality.time_utils

Time utilities for UTC standardization, bounds computation, and resampling.

Constitution compliance:
- Section 3: UTC canonical time; timezone-aware datetimes; preserve precision
- Section 10: Deterministic, reproducible behavior
- Section 11: Vectorized operations; single collect for bounds; no row loops

This module provides:
- TimeBounds dataclass: tz-aware UTC time range with sub-second precision
- Timezone utilities: ensure awareness, convert to UTC
- Bounds computation: Polars min/max aggregation with single collect
- Resampling: pandas boundary helper for hourly/custom mean aggregations
- Rolling statistics: centered rolling mean for QC flagging
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd
import polars as pl

from .exceptions import TimeError


@dataclass(frozen=True, slots=True)
class TimeBounds:
    """UTC-aware time bounds with full sub-second precision.

    Constitution Section 3: Preserve sub-second precision; always tz-aware UTC.

    Attributes
    ----------
    start : datetime
        Start timestamp (timezone-aware UTC).
    end : datetime
        End timestamp (timezone-aware UTC).

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> bounds = TimeBounds(
    ...     start=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    ...     end=datetime(2025, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
    ... )
    >>> bounds.start
    datetime.datetime(2025, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
    """

    start: datetime
    end: datetime


def ensure_timezone_aware(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware (attach UTC if naive).

    Constitution Section 3: UTC canonical time handling.

    Parameters
    ----------
    dt : datetime
        Input datetime (naive or aware).

    Returns
    -------
    datetime
        Timezone-aware datetime (UTC if input was naive; unchanged if already aware).

    Raises
    ------
    TimeError
        If input is not datetime-like.

    Examples
    --------
    >>> from datetime import datetime
    >>> naive = datetime(2025, 1, 1, 12, 0, 0)
    >>> ensure_timezone_aware(naive)
    datetime.datetime(2025, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)
    """
    from datetime import timezone as tz

    if not isinstance(dt, datetime):
        raise TimeError(f"Expected datetime object, got {type(dt).__name__}")

    # If already timezone-aware, return as-is
    if dt.tzinfo is not None:
        return dt

    # Attach UTC timezone to naive datetime
    return dt.replace(tzinfo=tz.utc)


def to_utc(dt: datetime) -> datetime:
    """Convert aware datetime to UTC (preserving instant).

    Naive datetimes are treated as UTC.
    Constitution Section 3: UTC standardization.

    Parameters
    ----------
    dt : datetime
        Input datetime (naive or aware).

    Returns
    -------
    datetime
        UTC datetime (converted if aware, unchanged if naive).

    Raises
    ------
    TimeError
        If input is not datetime-like.

    Examples
    --------
    >>> from datetime import datetime, timezone, timedelta
    >>> dt_est = datetime(2025, 1, 1, 12, 0, tzinfo=timezone(timedelta(hours=-5)))
    >>> to_utc(dt_est)
    datetime.datetime(2025, 1, 1, 17, 0, tzinfo=datetime.timezone.utc)
    """
    from datetime import timezone as tz

    if not isinstance(dt, datetime):
        raise TimeError(f"Expected datetime object, got {type(dt).__name__}")

    # If naive, treat as UTC and make aware
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz.utc)

    # If already UTC, return as-is
    if dt.tzinfo == tz.utc:
        return dt

    # Convert to UTC (preserving the instant in time)
    return dt.astimezone(tz.utc)


def compute_time_bounds(
    lazyframe: pl.LazyFrame,
    time_col: str = "datetime",
) -> TimeBounds:
    """Compute time bounds from Polars LazyFrame (single collect).

    Uses Polars min/max aggregation; ensures UTC timezone awareness.
    Constitution Section 3: Preserve sub-second precision.
    Constitution Section 11: Single collect only (NFR-M01).

    Parameters
    ----------
    lazyframe : pl.LazyFrame
        Input data with datetime column.
    time_col : str, default="datetime"
        Name of datetime column.

    Returns
    -------
    TimeBounds
        UTC-aware time bounds with precise min/max timestamps.

    Raises
    ------
    KeyError, Polars errors
        Underlying schema/column errors are surfaced (not masked).

    Examples
    --------
    >>> import polars as pl
    >>> from datetime import datetime
    >>> lf = pl.LazyFrame({
    ...     "datetime": [datetime(2025, 1, 1), datetime(2025, 1, 31)]
    ... })
    >>> bounds = compute_time_bounds(lf)
    >>> bounds.start
    datetime.datetime(2025, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
    """
    # Single collect operation for both min and max (Constitution Section 11: NFR-M01)
    # Use Polars aggregation to compute both min and max in one pass
    result = lazyframe.select(
        pl.col(time_col).min().alias("min_time"),
        pl.col(time_col).max().alias("max_time"),
    ).collect()

    # Extract min and max values
    min_time = result["min_time"][0]
    max_time = result["max_time"][0]

    # Convert to Python datetime if needed (Polars may return datetime objects)
    if hasattr(min_time, "to_pydatetime"):
        min_time = min_time.to_pydatetime()
    if hasattr(max_time, "to_pydatetime"):
        max_time = max_time.to_pydatetime()

    # Ensure UTC timezone awareness (Constitution Section 3)
    min_time_utc = to_utc(min_time)
    max_time_utc = to_utc(max_time)

    return TimeBounds(start=min_time_utc, end=max_time_utc)


def resample_mean(
    df: pd.DataFrame,
    rule: str = "1h",
    time_col: str = "datetime",
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Resample time series to regular intervals using mean aggregation.

    Uses pandas resample at boundary; numeric columns only.
    Constitution Section 11: Boundary pandas usage; input immutability.

    Parameters
    ----------
    df : pd.DataFrame
        Input data with datetime column/index.
    rule : str, default="1H"
        Resampling frequency (pandas offset alias).
    time_col : str, default="datetime"
        Name of datetime column (if not index).
    columns : list[str] | None, default=None
        Optional list of column names to resample. If None, resamples all
        numeric columns. If provided, only specified columns are resampled.

    Returns
    -------
    pd.DataFrame
        New DataFrame with resampled mean values (input unchanged).

    Raises
    ------
    ValueError, TypeError
        Datetime coercion or resampling errors surfaced.
    KeyError
        If specified column in `columns` parameter is not found.

    Examples
    --------
    >>> import pandas as pd
    >>> from datetime import datetime
    >>> # Hourly resampling workflow - all numeric columns
    >>> df = pd.DataFrame({
    ...     "datetime": pd.date_range("2025-01-01", periods=4, freq="30min"),
    ...     "conc": [10.5, 15.2, 12.3, 18.1],
    ...     "temp": [20.1, 21.3, 19.8, 22.5]
    ... })
    >>> resampled = resample_mean(df, rule="1h")
    >>> len(resampled)
    2
    >>> # Resample only specific columns
    >>> resampled_conc = resample_mean(df, rule="1h", columns=["conc"])
    >>> "conc" in resampled_conc.columns
    True
    >>> "temp" in resampled_conc.columns
    False
    >>> # Custom time column example
    >>> df_custom = pd.DataFrame({
    ...     "timestamp": pd.date_range("2025-01-01", periods=6, freq="10min"),
    ...     "pm25": [8.2, 9.1, 7.5, 10.3, 11.2, 9.8]
    ... })
    >>> hourly = resample_mean(df_custom, rule="1h", time_col="timestamp")
    >>> len(hourly)
    1
    """
    # Constitution Section 10, 15: Immutability - create copy to avoid mutating input
    df_copy = df.copy()

    # Handle empty DataFrame case
    if len(df_copy) == 0:
        return df_copy

    # Ensure datetime column is datetime type (surface coercion errors per contract)
    # This will raise ValueError or TypeError if conversion fails
    df_copy[time_col] = pd.to_datetime(df_copy[time_col])

    # Set datetime column as index for resampling
    df_copy = df_copy.set_index(time_col)

    # Constitution Section 11: Vectorized operations only
    # Determine which columns to resample
    if columns is not None:
        # Validate all specified columns exist
        missing_cols = set(columns) - set(df_copy.columns)
        if missing_cols:
            raise KeyError(f"Columns not found in DataFrame: {sorted(missing_cols)}")

        # Use only specified columns
        cols_to_resample = columns
    else:
        # Select all numeric columns for mean aggregation
        cols_to_resample = df_copy.select_dtypes(include=["number"]).columns.tolist()

    # Resample using pandas resample with mean aggregation
    if cols_to_resample:
        resampled = df_copy[cols_to_resample].resample(rule).mean()
    else:
        # No columns to resample - return empty resampled index
        resampled = df_copy.resample(rule).mean()

    # Reset index to restore time column (return as column, not index)
    resampled = resampled.reset_index()

    return resampled


def rolling_window_mean(
    df: pd.DataFrame,
    window: int = 3,
    time_col: str = "datetime",
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Compute centered rolling mean for QC flagging.

    Sorts by time first; uses centered window with min_periods=1.
    Constitution Section 11: Vectorized pandas operations; no row loops.

    Parameters
    ----------
    df : pd.DataFrame
        Input data with datetime column.
    window : int, default=3
        Rolling window size (must be >= 1).
    time_col : str, default="datetime"
        Name of datetime column for sorting.
    columns : list[str] | None, default=None
        Optional list of column names for rolling mean. If None, applies to all
        numeric columns. If provided, only specified columns are smoothed.

    Returns
    -------
    pd.DataFrame
        New DataFrame with rolling mean values (input unchanged).

    Raises
    ------
    ValueError
        If window < 1.
    KeyError
        If specified column in `columns` parameter is not found.

    Examples
    --------
    >>> import pandas as pd
    >>> from datetime import datetime
    >>> # QC spike detection workflow
    >>> df = pd.DataFrame({
    ...     "datetime": pd.date_range("2025-01-01", periods=5, freq="1h"),
    ...     "conc": [10.5, 15.2, 45.8, 12.3, 11.1]  # Spike at index 2
    ... })
    >>> rolled = rolling_window_mean(df, window=3)
    >>> # Compare spike to rolling mean to detect anomaly
    >>> spike_ratio = df["conc"].iloc[2] / rolled["conc"].iloc[2]
    >>> spike_ratio > 2.0  # Significant spike detected
    True
    >>> # Window=1 returns original values (no smoothing)
    >>> rolled_1 = rolling_window_mean(df, window=1)
    >>> (rolled_1["conc"] == df["conc"]).all()
    True
    >>> # Apply rolling mean to specific columns only
    >>> df_multi = pd.DataFrame({
    ...     "datetime": pd.date_range("2025-01-01", periods=5, freq="1h"),
    ...     "pm25": [10.5, 15.2, 45.8, 12.3, 11.1],
    ...     "temp": [20.0, 21.0, 22.0, 23.0, 24.0]
    ... })
    >>> rolled_pm25 = rolling_window_mean(df_multi, window=3, columns=["pm25"])
    >>> # temp column preserved but not smoothed
    """
    # Validate window parameter
    if window < 1:
        raise ValueError(f"window must be >= 1, got {window}")

    # Constitution Section 10, 15: Immutability - create copy to avoid mutating input
    df_copy = df.copy()

    # Handle empty DataFrame case
    if len(df_copy) == 0:
        return df_copy

    # Ensure datetime column is datetime type (surface parse errors per contract)
    # This will raise ValueError or TypeError if conversion fails
    df_copy[time_col] = pd.to_datetime(df_copy[time_col])

    # Constitution Section 11: Sort by time first (vectorized operation)
    df_copy = df_copy.sort_values(by=time_col).reset_index(drop=True)

    # Determine which columns to apply rolling mean
    if columns is not None:
        # Validate all specified columns exist
        missing_cols = set(columns) - set(df_copy.columns)
        if missing_cols:
            raise KeyError(f"Columns not found in DataFrame: {sorted(missing_cols)}")

        # Use only specified columns
        cols_to_smooth = columns
    else:
        # Select all numeric columns for rolling mean computation
        cols_to_smooth = df_copy.select_dtypes(include=["number"]).columns.tolist()

    # Compute centered rolling mean with min_periods=1
    # Constitution Section 11: Vectorized pandas operations
    if cols_to_smooth:
        # Apply rolling mean only to selected columns
        for col in cols_to_smooth:
            df_copy[col] = (
                df_copy[col].rolling(window=window, center=True, min_periods=1).mean()
            )

    return df_copy


__all__ = [
    "TimeBounds",
    "ensure_timezone_aware",
    "to_utc",
    "compute_time_bounds",
    "resample_mean",
    "rolling_window_mean",
]
