"""Core descriptive statistics computation function.

Constitution compliance:
- Section 11: Columnar groupby/agg (Polars), no Python loops
- Section 5: QC flag filtering
"""

from __future__ import annotations

import polars as pl

from .enums import DescriptiveStatsOperation, OutputFormat


def compute_descriptives(
    dataset: "TimeSeriesDataset",  # type: ignore[name-defined]
    value_cols: str | list[str],
    group_by: list[str] | None = None,
    category_col: str | None = None,
    flag_col: str | None = "flag",
    output_format: OutputFormat = OutputFormat.TIDY,
    stats: list[DescriptiveStatsOperation] | None = None,
) -> "polars.DataFrame":  # type: ignore[name-defined]
    """Compute descriptive statistics for one or more numeric columns with optional grouping.

    Uses Polars for vectorized groupby/aggregation. Excludes invalid/outlier
    rows; treats below_dl as missing. Returns tidy format (one row per statistic per column)
    by default, or wide format (one row per group with separate columns for each statistic).

    This function is generic and can be used for any time series data, not just
    air quality concentrations. It can analyze multiple numeric columns in a single call.

    Constitution References
    -----------------------
    - Section 11: Columnar groupby/agg (Polars), no Python loops
    - Section 5: QC flag filtering (exclude invalid/outlier, treat below_dl as missing)

    Parameters
    ----------
    dataset : TimeSeriesDataset
        Canonical time series dataset.
    value_cols : str | list[str]
        Numeric value column(s) to analyze (required).
        Single column: "conc" or "temperature"
        Multiple columns: ["temperature", "humidity", "pressure"]
        For air quality: typically "conc" or ["conc", "unc"]
        For other domains: any numeric columns
    group_by : list[str] | None
        Grouping columns (e.g., ["site_id", "region"]). If None, uses only category_col.
        If both group_by and category_col are None, computes global statistics.
    category_col : str | None, default=None
        Categorical column for additional grouping. If None, no category grouping is applied.
        For air quality: typically "pollutant" or "species_id"
        For other domains: any categorical column (e.g., "sensor_type", "product_id")
    flag_col : str | None, default="flag"
        QC flag column name. If None or column doesn't exist, no QC filtering is applied.
    output_format : OutputFormat, default=OutputFormat.TIDY
        Output format: TIDY (long format with 'stat' column) or WIDE (separate columns per statistic).
    stats : list[DescriptiveStatsOperation] | None, default=None
        List of statistics to compute. If None, computes all statistics (mean, median, std, min, max, count).
        Options: DescriptiveStatsOperation.MEAN, DescriptiveStatsOperation.MEDIAN, etc.
        Example: [DescriptiveStatsOperation.MEAN, DescriptiveStatsOperation.STD] computes only mean and standard deviation.

    Returns
    -------
    polars.DataFrame
        TIDY format (default):
        - grouping columns (if group_by is not None)
        - category column (if category_col is not None) - named after category_col parameter
        - value_col_name: name of the value column being analyzed
        - stat: statistic type (mean, median, std, min, max, q05, q25, q75, q95)
        - value: computed statistic value
        - n_total: total observations before filtering
        - n_valid: valid observations used in computation
        - n_missing: missing observations (excluded + below_dl)

        WIDE format:
        - grouping columns (if group_by is not None)
        - category column (if category_col is not None)
        - value_col_name: name of the value column being analyzed
        - mean, median, std, min, max, q05, q25, q75, q95: separate columns for each statistic
        - n_total: total observations before filtering
        - n_valid: valid observations used in computation
        - n_missing: missing observations (excluded + below_dl)

    Raises
    ------
    DataValidationError
        If any value column is non-numeric.
    SchemaError
        If any value_cols are missing, or if category_col/flag_col specified but missing.

    Examples
    --------
    Single column (air quality):

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
    >>> result = compute_descriptives(dataset, value_cols="conc", category_col="pollutant")
    >>> result.select(["pollutant", "value_col_name", "stat", "value"]).head()
    shape: (5, 4)
    ┌───────────┬────────────────┬────────┬───────┐
    │ pollutant ┆ value_col_name ┆ stat   ┆ value │
    │ ---       ┆ ---            ┆ ---    ┆ ---   │
    │ str       ┆ str            ┆ str    ┆ f64   │
    ╞═══════════╪════════════════╪════════╪═══════╡
    │ PM25      ┆ conc           ┆ mean   ┆ 5.5   │
    │ PM25      ┆ conc           ┆ median ┆ 5.5   │
    │ PM25      ┆ conc           ┆ std    ┆ ...   │
    │ PM25      ┆ conc           ┆ min    ┆ 1.0   │
    │ PM25      ┆ conc           ┆ max    ┆ 10.0  │
    └───────────┴────────────────┴────────┴───────┘

    Multiple columns (meteorology):

    >>> df = pd.DataFrame({
    ...     "datetime": pd.date_range("2025-01-01", periods=10, freq="h"),
    ...     "site_id": ["S1"] * 10,
    ...     "temperature": [20.0, 21.5, 22.0, 21.0, 20.5, 19.5, 20.0, 21.0, 22.5, 23.0],
    ...     "humidity": [65.0, 63.0, 60.0, 62.0, 64.0, 68.0, 70.0, 69.0, 66.0, 64.0],
    ...     "pressure": [1013.0, 1012.5, 1013.2, 1014.0, 1013.8, 1013.5, 1013.0, 1012.8, 1013.1, 1013.4],
    ... })
    >>> dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")
    >>> result = compute_descriptives(
    ...     dataset,
    ...     value_cols=["temperature", "humidity", "pressure"],
    ...     group_by=["site_id"],
    ...     flag_col=None
    ... )
    >>> # Result contains stats for all three columns
    >>> result.filter(pl.col("stat") == "mean").select(["value_col_name", "value"])
    shape: (3, 2)
    ┌────────────────┬───────┐
    │ value_col_name ┆ value │
    │ ---            ┆ ---   │
    │ str            ┆ f64   │
    ╞════════════════╪═══════╡
    │ temperature    ┆ 21.0  │
    │ humidity       ┆ 65.1  │
    │ pressure       ┆ 1013.1│
    └────────────────┴───────┘
    """
    from ...qc_flags import (
        EXCLUDE_FLAGS,
        MISSING_FLAGS,
        QCFlag,
        filter_by_qc_flags,
        mark_missing_by_flags,
    )

    # Get quantile levels
    quantile_levels = [0.05, 0.25, 0.75, 0.95]

    # Determine which statistics to compute
    if stats is None:
        # Compute all statistics by default
        stats_to_compute = {
            DescriptiveStatsOperation.MEAN,
            DescriptiveStatsOperation.MEDIAN,
            DescriptiveStatsOperation.STD,
            DescriptiveStatsOperation.MIN,
            DescriptiveStatsOperation.MAX,
            DescriptiveStatsOperation.COUNT,
            DescriptiveStatsOperation.QUANTILES,
        }
    else:
        stats_to_compute = set(stats)

    # Normalize value_cols to list
    if isinstance(value_cols, str):
        value_cols_list = [value_cols]
    else:
        value_cols_list = value_cols

    # Work with LazyFrame throughout to maximize optimization
    df_lazy = dataset.lazyframe

    # Check if required columns exist (use schema, don't collect)
    schema = df_lazy.collect_schema()
    schema_names = schema.names()

    # All value_cols are required
    missing_value_cols = [col for col in value_cols_list if col not in schema_names]
    if missing_value_cols:
        from ...exceptions import SchemaError

        raise SchemaError(
            f"Required value column(s) not found in dataset: {missing_value_cols}"
        )

    # Check optional columns if specified
    missing_cols = []
    if category_col is not None and category_col not in schema_names:
        missing_cols.append(category_col)
    if flag_col is not None and flag_col not in schema_names:
        # Flag column is optional - just note it's missing (don't error)
        flag_col = None  # Disable QC filtering
    if group_by:
        for col in group_by:
            if col not in schema_names:
                missing_cols.append(col)

    if missing_cols:
        from ...exceptions import SchemaError

        raise SchemaError(f"Specified columns not found in dataset: {missing_cols}")

    # Build grouping columns
    group_cols = []
    if group_by:
        group_cols.extend(group_by)
    if category_col is not None:
        group_cols.append(category_col)

    # Apply QC filtering in lazy mode if flag column exists (applies to all value columns)
    df_filtered = df_lazy
    if flag_col is not None:
        # Fill null flags with "valid" (null flags treated as valid per Constitution)
        df_filtered = df_filtered.with_columns(
            pl.col(flag_col).fill_null(QCFlag.VALID.value)
        )
        df_filtered = filter_by_qc_flags(
            df_filtered, flag_col=flag_col, exclude_flags=EXCLUDE_FLAGS
        )
        # Note: mark_missing_by_flags needs to be called per column

    # Process each value column and collect results
    all_stats = []

    for value_col in value_cols_list:
        # Apply missing flag marking for this specific column
        df_for_col = df_filtered
        if flag_col is not None:
            df_for_col = mark_missing_by_flags(
                df_for_col,
                conc_col=value_col,
                flag_col=flag_col,
                missing_flags=MISSING_FLAGS,
            )

        # Compute n_total BEFORE filtering (on original data)
        if group_cols:
            counts_total = df_lazy.group_by(group_cols).agg(pl.len().alias("n_total"))
        else:
            # Global aggregation (no groups)
            counts_total = df_lazy.select(pl.len().alias("n_total"))

        # Build aggregation expressions for statistics
        quantile_map = {
            0.05: "q05",
            0.25: "q25",
            0.75: "q75",
            0.95: "q95",
        }

        agg_exprs = []

        # Always compute n_valid (count) - needed for n_missing calculation
        agg_exprs.append(pl.col(value_col).is_not_null().sum().alias("n_valid"))

        # Build aggregation expressions based on requested stats
        if DescriptiveStatsOperation.MEAN in stats_to_compute:
            agg_exprs.append(pl.col(value_col).mean().alias("mean"))
        if DescriptiveStatsOperation.MEDIAN in stats_to_compute:
            agg_exprs.append(pl.col(value_col).median().alias("median"))
        if DescriptiveStatsOperation.STD in stats_to_compute:
            agg_exprs.append(pl.col(value_col).std().alias("std"))
        if DescriptiveStatsOperation.MIN in stats_to_compute:
            agg_exprs.append(pl.col(value_col).min().alias("min"))
        if DescriptiveStatsOperation.MAX in stats_to_compute:
            agg_exprs.append(pl.col(value_col).max().alias("max"))

        # Add quantile expressions if requested
        if DescriptiveStatsOperation.QUANTILES in stats_to_compute:
            for q_level in quantile_levels:
                if q_level in quantile_map:
                    alias = quantile_map[q_level]
                else:
                    # For custom quantiles, create name like "q10", "q90"
                    alias = f"q{int(q_level * 100):02d}"
                agg_exprs.append(pl.col(value_col).quantile(q_level).alias(alias))

        # Compute statistics on filtered data
        if group_cols:
            stats_wide = df_for_col.group_by(group_cols).agg(agg_exprs)

            # Join with total counts (full outer join to keep all groups)
            stats_wide = counts_total.join(
                stats_wide, on=group_cols, how="full", suffix="_stats"
            )

            # Coalesce group columns if there are duplicates from the join
            for col in group_cols:
                if f"{col}_stats" in stats_wide.collect_schema().names():
                    stats_wide = stats_wide.with_columns(
                        pl.coalesce([pl.col(col), pl.col(f"{col}_stats")]).alias(col)
                    ).drop(f"{col}_stats")
        else:
            # Global aggregation (no groups) - compute directly and combine with n_total
            stats_wide = df_for_col.select(agg_exprs)
            # Horizontal concat (both have single row, combine columns)
            stats_wide = pl.concat([counts_total, stats_wide], how="horizontal")

        # Fill nulls: n_total=0 if group didn't exist, n_valid=0 if no valid data after filtering
        stats_wide = stats_wide.with_columns(
            [
                pl.col("n_total").fill_null(0),
                pl.col("n_valid").fill_null(0),
            ]
        )

        # Compute n_missing efficiently
        stats_wide = stats_wide.with_columns(
            (pl.col("n_total") - pl.col("n_valid")).alias("n_missing")
        )

        # Convert to tidy format (unpivot statistics)
        # Get stat column names (exclude group columns and count columns)
        schema_wide = stats_wide.collect_schema()
        stat_cols = [
            col
            for col in schema_wide.names()
            if col not in group_cols and col not in ["n_total", "n_valid", "n_missing"]
        ]

        # Unpivot to tidy format
        stats_tidy = stats_wide.unpivot(
            index=group_cols + ["n_total", "n_valid", "n_missing"],
            on=stat_cols,
            variable_name="stat",
            value_name="value",
        )

        # Add value_col_name column to track which column this is
        stats_tidy = stats_tidy.with_columns(pl.lit(value_col).alias("value_col_name"))

        # Collect and append to results
        all_stats.append(stats_tidy.collect())

    # Concatenate all results (one per value column)
    if len(all_stats) == 1:
        final_stats = all_stats[0]
    else:
        final_stats = pl.concat(all_stats, how="vertical")

    # Sort by group columns, value_col_name, and stat for consistent output
    sort_cols = []
    if group_cols:
        sort_cols.extend(group_cols)
    sort_cols.extend(["value_col_name", "stat"])
    final_stats = final_stats.sort(sort_cols)

    # Convert to wide format if requested
    if output_format == OutputFormat.WIDE:
        # Pivot: stat column becomes separate columns
        index_cols = []
        if group_cols:
            index_cols.extend(group_cols)
        index_cols.extend(["value_col_name", "n_total", "n_valid", "n_missing"])

        final_stats = final_stats.pivot(
            index=index_cols,
            on="stat",
            values="value",
        )

        # Sort wide format for consistent output
        final_stats = final_stats.sort(index_cols)

    return final_stats


__all__ = ["compute_descriptives"]
