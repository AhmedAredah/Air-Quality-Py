"""air_quality.analysis.descriptive

Descriptive statistics primitives (mean, median, std, quantiles, counts).

Constitution compliance:
- Section 11: Columnar groupby/agg (Polars), no Python loops
- Section 5: QC flag filtering (exclude invalid/outlier, treat below_dl as missing)
"""

from __future__ import annotations

from enum import Enum


class StatisticType(str, Enum):
    """Descriptive statistics computed by the descriptive module.

    Constitution References
    -----------------------
    - Section 7: Module output standards

    Statistics:
    - MEAN: Arithmetic mean
    - MEDIAN: 50th percentile
    - STD: Standard deviation
    - MIN: Minimum value
    - MAX: Maximum value
    - Q05: 5th percentile
    - Q25: 25th percentile (first quartile)
    - Q75: 75th percentile (third quartile)
    - Q95: 95th percentile
    """

    MEAN = "mean"
    MEDIAN = "median"
    STD = "std"
    MIN = "min"
    MAX = "max"
    Q05 = "q05"
    Q25 = "q25"
    Q75 = "q75"
    Q95 = "q95"


# Quantile levels for descriptive statistics
DEFAULT_QUANTILES: tuple[float, ...] = (0.05, 0.25, 0.75, 0.95)
"""Default quantile levels: 5th, 25th, 75th, 95th percentiles."""

# Statistics computed by descriptive module
DESCRIPTIVE_STATS: tuple[StatisticType, ...] = (
    StatisticType.MEAN,
    StatisticType.MEDIAN,
    StatisticType.STD,
    StatisticType.MIN,
    StatisticType.MAX,
    StatisticType.Q05,
    StatisticType.Q25,
    StatisticType.Q75,
    StatisticType.Q95,
)
"""Standard statistics computed for descriptive summaries."""


__all__ = [
    "StatisticType",
    "DEFAULT_QUANTILES",
    "DESCRIPTIVE_STATS",
    "get_quantile_levels",
    "compute_descriptives",
]


def get_quantile_levels(
    quantiles: tuple[float, ...] | None = None,
) -> tuple[float, ...]:
    """Get quantile levels for descriptive statistics.

    Helper function to return default or custom quantile levels.

    Constitution References
    -----------------------
    - Section 7: Configuration validation

    Parameters
    ----------
    quantiles : tuple[float, ...] | None
        Custom quantile levels (e.g., (0.25, 0.50, 0.75)).
        If None, returns DEFAULT_QUANTILES (0.05, 0.25, 0.75, 0.95).

    Returns
    -------
    tuple[float, ...]
        Quantile levels to compute.

    Examples
    --------
    >>> get_quantile_levels()
    (0.05, 0.25, 0.75, 0.95)
    >>> get_quantile_levels((0.1, 0.9))
    (0.1, 0.9)
    """
    if quantiles is None:
        return DEFAULT_QUANTILES
    return quantiles


def compute_descriptives(
    dataset: "TimeSeriesDataset",  # type: ignore[name-defined]
    group_by: list[str] | None = None,
    pollutant_col: str = "pollutant",
    conc_col: str = "conc",
    flag_col: str = "flag",
    quantiles: tuple[float, ...] | None = None,
) -> "polars.DataFrame":  # type: ignore[name-defined]
    """Compute descriptive statistics per pollutant and grouping keys.

    Uses Polars for vectorized groupby/aggregation. Excludes invalid/outlier
    rows; treats below_dl as missing. Returns tidy format (one row per statistic).

    Constitution References
    -----------------------
    - Section 11: Columnar groupby/agg (Polars), no Python loops
    - Section 5: QC flag filtering (exclude invalid/outlier, treat below_dl as missing)

    Parameters
    ----------
    dataset : TimeSeriesDataset
        Canonical time series dataset.
    group_by : list[str] | None
        Additional grouping columns (e.g., ["site_id"]). If None, global aggregation.
        Pollutant is always included in grouping.
    pollutant_col : str, default="pollutant"
        Pollutant identifier column name.
    conc_col : str, default="conc"
        Concentration value column name.
    flag_col : str, default="flag"
        QC flag column name.
    quantiles : tuple[float, ...] | None
        Quantile levels to compute. If None, uses DEFAULT_QUANTILES.

    Returns
    -------
    polars.DataFrame
        Tidy dataframe with columns:
        - grouping columns (if group_by is not None)
        - pollutant: pollutant identifier
        - stat: statistic type (mean, median, std, min, max, q05, q25, q75, q95)
        - value: computed statistic value
        - n_total: total observations before filtering
        - n_valid: valid observations used in computation
        - n_missing: missing observations (excluded + below_dl)

    Raises
    ------
    DataValidationError
        If concentration column is non-numeric.
    SchemaError
        If required columns are missing.

    Examples
    --------
    >>> import pandas as pd
    >>> from air_quality.dataset.time_series import TimeSeriesDataset
    >>> from air_quality.qc_flags import QCFlag
    >>> df = pd.DataFrame({
    ...     "datetime": pd.date_range("2025-01-01", periods=10, freq="h"),
    ...     "site_id": ["S1"] * 10,
    ...     "pollutant": ["PM25"] * 10,
    ...     "conc": list(range(1, 11)),
    ...     "flag": [QCFlag.VALID.value] * 10,
    ... })
    >>> dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")
    >>> result = compute_descriptives(dataset, group_by=None)
    >>> result.select(["pollutant", "stat", "value"]).head()
    shape: (5, 3)
    ┌───────────┬────────┬───────┐
    │ pollutant ┆ stat   ┆ value │
    │ ---       ┆ ---    ┆ ---   │
    │ str       ┆ str    ┆ f64   │
    ╞═══════════╪════════╪═══════╡
    │ PM25      ┆ mean   ┆ 5.5   │
    │ PM25      ┆ median ┆ 5.5   │
    │ PM25      ┆ std    ┆ ...   │
    │ PM25      ┆ min    ┆ 1.0   │
    │ PM25      ┆ max    ┆ 10.0  │
    └───────────┴────────┴───────┘
    """
    import polars as pl
    from ..qc_flags import (
        filter_by_qc_flags,
        mark_missing_by_flags,
        EXCLUDE_FLAGS,
        MISSING_FLAGS,
        QCFlag,
    )

    # Get quantile levels
    quantile_levels = get_quantile_levels(quantiles)

    # Get dataframe from dataset (collect LazyFrame)
    df = dataset.lazyframe.collect()

    # Check if required columns exist
    required_cols = [pollutant_col, conc_col]
    if flag_col and flag_col in df.columns:
        required_cols.append(flag_col)

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        from ..exceptions import SchemaError

        raise SchemaError(f"Missing required columns: {missing_cols}")

    # Filter out invalid/outlier flags and mark below_dl as missing
    if flag_col and flag_col in df.columns:
        # Convert to LazyFrame for filtering
        df_lazy = df.lazy()
        # Fill null flags with "valid" (null flags treated as valid per Constitution)
        df_lazy = df_lazy.with_columns(
            pl.col(flag_col).fill_null(QCFlag.VALID.value).alias(flag_col)
        )
        df_lazy = filter_by_qc_flags(
            df_lazy, flag_col=flag_col, exclude_flags=EXCLUDE_FLAGS
        )
        # Mark below_dl as missing (set conc to null)
        df_lazy = mark_missing_by_flags(
            df_lazy, conc_col=conc_col, flag_col=flag_col, missing_flags=MISSING_FLAGS
        )
        df_filtered = df_lazy.collect()
    else:
        df_filtered = df

    # Also filter out NaN values in concentration column for valid count
    df_valid = df_filtered.filter(pl.col(conc_col).is_not_null())

    # Build grouping columns (always include pollutant)
    group_cols = [pollutant_col]
    if group_by:
        group_cols = group_by + [pollutant_col]

    # Compute counts per group
    counts = df.group_by(group_cols).agg(
        [
            pl.len().alias("n_total"),
        ]
    )

    # Compute valid counts (after filtering flags AND NaN values)
    valid_counts = df_valid.group_by(group_cols).agg(
        [
            pl.len().alias("n_valid"),
        ]
    )

    # Merge counts
    counts = counts.join(valid_counts, on=group_cols, how="left").with_columns(
        [
            pl.col("n_valid").fill_null(0),
            (pl.col("n_total") - pl.col("n_valid").fill_null(0)).alias("n_missing"),
        ]
    )

    # Compute statistics on filtered data (excludes flags AND NaN)
    agg_exprs = [
        pl.col(conc_col).mean().alias("mean"),
        pl.col(conc_col).median().alias("median"),
        pl.col(conc_col).std().alias("std"),
        pl.col(conc_col).min().alias("min"),
        pl.col(conc_col).max().alias("max"),
    ]

    # Add quantile expressions
    quantile_map = {
        0.05: "q05",
        0.25: "q25",
        0.75: "q75",
        0.95: "q95",
    }
    for q_level in quantile_levels:
        # Use consistent naming for quantiles
        if q_level in quantile_map:
            alias = quantile_map[q_level]
        else:
            # For custom quantiles, create name like "q10", "q90"
            alias = f"q{int(q_level * 100):02d}"
        agg_exprs.append(pl.col(conc_col).quantile(q_level).alias(alias))

    stats_wide = df_valid.group_by(group_cols).agg(agg_exprs)

    # Merge with counts (use "left" to prefer stats_wide, then fill missing)
    # For groups with no valid data, stats_wide won't have them, so we need "full"
    # but we need to handle duplicate columns from the join
    stats_wide = stats_wide.join(counts, on=group_cols, how="full", suffix="_counts")

    # Coalesce group columns (prefer non-null from either side)
    for col in group_cols:
        if f"{col}_counts" in stats_wide.columns:
            stats_wide = stats_wide.with_columns(
                pl.coalesce([pl.col(col), pl.col(f"{col}_counts")]).alias(col)
            ).drop(f"{col}_counts")

    # Fill null count columns with 0 for groups that had no data
    for count_col in ["n_total", "n_valid", "n_missing"]:
        stats_wide = stats_wide.with_columns(pl.col(count_col).fill_null(0))

    # Convert to tidy format (unpivot statistics)
    # Get stat column names (exclude group columns and count columns)
    value_cols = [
        col
        for col in stats_wide.columns
        if col not in group_cols and col not in ["n_total", "n_valid", "n_missing"]
    ]

    # Unpivot to tidy format
    stats_tidy = stats_wide.unpivot(
        index=group_cols + ["n_total", "n_valid", "n_missing"],
        on=value_cols,
        variable_name="stat",
        value_name="value",
    )

    # Sort by group columns and stat for consistent output
    sort_cols = group_cols + ["stat"]
    stats_tidy = stats_tidy.sort(sort_cols)

    return stats_tidy
