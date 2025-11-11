"""Core trend analysis computation function.

Constitution compliance:
- Section 11: Closed-form OLS via sufficient statistics
- Section 15: Unit enforcement for slopes
- Section 3: Calendar-aware time semantics
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import polars as pl

from ...dataset.time_series import TimeSeriesDataset
from ...exceptions import UnitError
from ...qc_flags import filter_by_qc_flags, mark_missing_by_flags
from ...units import TimeUnit, compute_elapsed_time
from .constants import (
    ALLOWED_TIME_UNITS,
    DEFAULT_MIN_DURATION_YEARS,
    DEFAULT_MIN_SAMPLES,
)


def compute_linear_trend(
    dataset: TimeSeriesDataset,
    time_unit: TimeUnit,
    category_col: str = "pollutant",
    datetime_col: str = "datetime",
    value_col: str = "concentration",
    flag_col: str = "flag",
    group_by: Optional[list[str]] = None,
    min_samples: int = DEFAULT_MIN_SAMPLES,
    min_duration_years: float = DEFAULT_MIN_DURATION_YEARS,
    allow_missing_units: bool = False,
) -> pl.DataFrame:
    """Compute linear trend (OLS regression: value ~ time) for time series data.

    Constitution compliance:
    - Section 11: Closed-form OLS using sufficient statistics (no iterative solvers)
    - Section 15: Unit enforcement for slopes (value_unit / time_unit)
    - Section 3: Calendar-aware time using compute_elapsed_time()

    Parameters
    ----------
    dataset : TimeSeriesDataset
        Time series dataset with datetime, value, and category columns.
    time_unit : TimeUnit
        Time unit for trend analysis (hour/day/calendar_month/calendar_year).
    category_col : str, default="pollutant"
        Column name for category identifier (e.g., pollutant, variable name).
    datetime_col : str, default="datetime"
        Column name for datetime timestamps.
    value_col : str, default="concentration"
        Column name for numeric values to analyze.
    flag_col : str, default="flag"
        Column name for QC flags.
    group_by : list[str] | None, default=None
        Additional grouping columns beyond category.
    min_samples : int, default=3
        Minimum number of valid observations to compute trend.
    min_duration_years : float, default=1.0
        Minimum duration in years (shorter durations flagged).
    allow_missing_units : bool, default=False
        If True, allow missing units (slope_units will be "unknown").

    Returns
    -------
    pl.DataFrame
        Trend results with columns:
        - {category_col}: Category identifier
        - [group_by columns]: If provided
        - slope: Slope (value_unit per time_unit)
        - intercept: Y-intercept
        - r_squared: R² coefficient of determination
        - n: Number of observations used
        - duration_years: Duration of time series in years
        - start_time: Start timestamp
        - end_time: End timestamp
        - short_duration_flag: True if duration < min_duration_years
        - low_n_flag: True if n < min_samples (but still computed)
        - slope_units: Units for slope (value_unit/time_unit) or "unknown"

    Raises
    ------
    UnitError
        If value_col has no unit defined (unless allow_missing_units=True).

    Notes
    -----
    - QC filtering: Filters out rows with qc_flag != 0
    - Time conversion: Uses compute_elapsed_time() for calendar-aware semantics
    - OLS formula: slope = (n*Σxy - ΣxΣy) / (n*Σx² - (Σx)²)
    - R² formula: 1 - (SSres / SStot)
    - Groups with n < min_samples return empty result

    Examples
    --------
    >>> import polars as pl
    >>> from datetime import datetime, timedelta
    >>> from air_quality.dataset.time_series import TimeSeriesDataset
    >>> from air_quality.units import TimeUnit
    >>> df = pl.DataFrame({
    ...     "datetime": [datetime(2024, 1, 1) + timedelta(days=i) for i in range(10)],
    ...     "concentration": [2.0 * i + 5.0 for i in range(10)],
    ...     "pollutant": ["NO2"] * 10,
    ...     "flag": ["valid"] * 10,
    ... })
    >>> dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")
    >>> result = compute_linear_trend(dataset, TimeUnit.DAY, value_col="concentration")
    # slope ≈ 2.0, intercept ≈ 5.0, r_squared ≈ 1.0
    """
    # Validate time unit
    if time_unit not in ALLOWED_TIME_UNITS:
        raise ValueError(
            f"time_unit must be one of {[u.value for u in ALLOWED_TIME_UNITS]}, got {time_unit.value}"
        )

    # Extract LazyFrame from dataset
    data = dataset.lazyframe

    # Check units from dataset
    value_units: Optional[str] = None
    column_units = dataset.column_units
    if column_units is not None and value_col in column_units:
        unit_value = column_units[value_col]
        # Extract symbol string from Unit enum
        value_units = (
            unit_value.symbol if hasattr(unit_value, "symbol") else str(unit_value)
        )
    elif not allow_missing_units:
        raise UnitError(
            f"Column '{value_col}' has no unit defined. "
            f"Use allow_missing_units=True to proceed without units."
        )

    # Determine slope units
    slope_units: str
    if value_units:
        slope_units = f"{value_units}/{time_unit.value}"
    else:
        slope_units = f"unknown/{time_unit.value}"

    # QC filtering
    data_filtered = filter_by_qc_flags(data, flag_col=flag_col)
    # Materialize to avoid complex lazy plan issues
    data_filtered = data_filtered.collect().lazy()
    data_filtered = mark_missing_by_flags(
        data_filtered, flag_col=flag_col, conc_col=value_col
    )

    # Set up grouping columns
    group_cols = [category_col]
    if group_by:
        group_cols.extend(group_by)

    # Collect data to pandas for time conversion (compute_elapsed_time requires pd.Timestamp)
    df_pandas = data_filtered.collect().to_pandas()

    # Convert to pandas timestamps if needed
    if not pd.api.types.is_datetime64_any_dtype(df_pandas[datetime_col]):
        df_pandas[datetime_col] = pd.to_datetime(df_pandas[datetime_col])

    # Group by pollutant (and other group_by columns)
    results_list = []

    for group_key, group_df in df_pandas.groupby(group_cols):
        # Ensure we have a tuple for group_key
        if not isinstance(group_key, tuple):
            group_key = (group_key,)

        # Filter out nulls in value column
        group_df = group_df[group_df[value_col].notna()].copy()

        # Check min samples
        n = len(group_df)
        if n < min_samples:
            continue  # Skip this group

        # Sort by datetime
        group_df = group_df.sort_values(datetime_col)

        # Get start and end times
        start_time = group_df[datetime_col].iloc[0]
        end_time = group_df[datetime_col].iloc[-1]

        # Convert timestamps to numeric time values using compute_elapsed_time
        # Set t=0 at start_time
        group_df["time_numeric"] = group_df[datetime_col].apply(
            lambda dt: compute_elapsed_time(start_time, pd.Timestamp(dt), time_unit)
        )

        # Compute duration in years (for flagging)
        duration_years = compute_elapsed_time(
            start_time, end_time, TimeUnit.CALENDAR_YEAR
        )

        # Extract x (time) and y (value)
        x = group_df["time_numeric"].values
        y = group_df[value_col].values

        # Compute sufficient statistics for OLS
        n_obs = len(x)
        sum_x = x.sum()  # type: ignore[union-attr]
        sum_y = y.sum()  # type: ignore[union-attr]
        sum_xy = (x * y).sum()  # type: ignore[operator]
        sum_x2 = (x * x).sum()  # type: ignore[operator]
        sum_y2 = (y * y).sum()  # type: ignore[operator]

        # Compute slope and intercept using closed-form OLS
        # slope = (n*Σxy - ΣxΣy) / (n*Σx² - (Σx)²)
        denominator = n_obs * sum_x2 - sum_x * sum_x

        if abs(denominator) < 1e-12:
            # Constant x values (all times the same) - undefined slope
            slope = 0.0
            intercept = sum_y / n_obs if n_obs > 0 else 0.0
            r_squared = None
        else:
            slope = (n_obs * sum_xy - sum_x * sum_y) / denominator
            intercept = (sum_y - slope * sum_x) / n_obs

            # Compute R²: 1 - (SSres / SStot)
            y_pred = slope * x + intercept
            ss_res = ((y - y_pred) ** 2).sum()

            y_mean = sum_y / n_obs
            ss_tot = ((y - y_mean) ** 2).sum()

            if abs(ss_tot) < 1e-12:
                # Constant y values - R² is undefined (or 0)
                r_squared = None
            else:
                r_squared = 1.0 - (ss_res / ss_tot)

        # Flags
        short_duration_flag = duration_years < min_duration_years
        low_n_flag = (
            n_obs < min_samples
        )  # This will always be False here since we skip if n < min_samples

        # Build result record
        result_record = {}
        for i, col_name in enumerate(group_cols):
            result_record[col_name] = group_key[i]

        result_record.update(
            {
                "slope": slope,
                "intercept": intercept,
                "r_squared": r_squared,
                "n": n_obs,
                "duration_years": duration_years,
                "start_time": start_time,
                "end_time": end_time,
                "short_duration_flag": short_duration_flag,
                "low_n_flag": low_n_flag,
                "slope_units": slope_units,
            }
        )

        results_list.append(result_record)

    # Convert results to Polars DataFrame
    if results_list:
        results_df = pl.DataFrame(results_list)
    else:
        # Empty result with correct schema
        schema: dict[str, type[pl.DataType]] = {col: pl.Utf8 for col in group_cols}
        schema.update(
            {
                "slope": pl.Float64,
                "intercept": pl.Float64,
                "r_squared": pl.Float64,
                "n": pl.Int64,
                "duration_years": pl.Float64,
                "start_time": pl.Datetime,
                "end_time": pl.Datetime,
                "short_duration_flag": pl.Boolean,
                "low_n_flag": pl.Boolean,
                "slope_units": pl.Utf8,
            }
        )
        results_df = pl.DataFrame(schema=schema)

    return results_df


__all__ = ["compute_linear_trend"]
