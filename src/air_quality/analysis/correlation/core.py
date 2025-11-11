"""Core correlation computation function.

Constitution compliance:
- Section 11: Vectorized correlation via pivot/covariance
- Section 15: Units presence checks (configurable override)
"""

from __future__ import annotations

import polars as pl

from .constants import DEFAULT_MIN_SAMPLES
from .enums import CorrelationOperation, OutputFormat
from .utils import compute_correlations_for_group, generate_ordered_pairs


def compute_pairwise(
    dataset: "TimeSeriesDataset",  # type: ignore[name-defined]  # noqa: F821
    group_by: list[str] | None,
    correlation_type: CorrelationOperation = CorrelationOperation.PEARSON,
    category_col: str = "pollutant",
    value_cols: str | list[str] = "conc",
    flag_col: str = "flag",
    min_samples: int = DEFAULT_MIN_SAMPLES,
    allow_missing_units: bool = False,
    output_format: OutputFormat = OutputFormat.TIDY,
) -> "polars.DataFrame | pandas.DataFrame":  # type: ignore[name-defined]  # noqa: F821
    """Compute pairwise correlations across categories with ordered unique pairs.

    Implements vectorized correlation computation with QC-aware filtering and
    optional unit enforcement. Returns ordered pairs (var_x <= var_y) including
    diagonal (self-correlation). Supports multiple value columns and output formats
    (tidy or wide correlation matrix).

    Constitution References
    -----------------------
    - Section 5: QC flag filtering (exclude INVALID, OUTLIER; treat BELOW_DL as missing)
    - Section 11: Vectorized operations via pivot and correlation matrices
    - Section 15: Unit presence checks (configurable override)

    Parameters
    ----------
    dataset : TimeSeriesDataset
        Input dataset with time series data in canonical long format.
    group_by : list[str] | None
        Grouping columns (e.g., ["site_id"]). None for global correlation.
    correlation_type : CorrelationOperation
        Correlation method: CorrelationOperation.PEARSON or CorrelationOperation.SPEARMAN.
    category_col : str
        Column identifying categories for correlation (e.g., "pollutant").
    value_cols : str | list[str]
        Numeric value column(s) to analyze (e.g., "conc" or ["conc", "unc"]).
        Single column: "conc" or "temperature"
        Multiple columns: ["conc", "unc"] or ["temperature", "humidity"]
    flag_col : str
        Column containing QC flags.
    min_samples : int
        Minimum number of valid observations to compute correlation.
    allow_missing_units : bool
        If False, raises UnitError if value_cols lack unit metadata.
        If True, allows correlation without units (for dimensionless data).
    output_format : OutputFormat, default=OutputFormat.TIDY
        Output format: TIDY (long format) or WIDE (correlation matrix).

    Returns
    -------
    polars.DataFrame | pandas.DataFrame
        TIDY format (default):
        - group_by columns (if provided)
        - value_col_name: name of the value column being analyzed
        - var_x: First variable in pair (alphabetically)
        - var_y: Second variable in pair (var_x <= var_y)
        - correlation: Correlation coefficient
        - n: Number of valid pairwise observations

        WIDE format (correlation matrix):
        - group_by columns (if provided)
        - value_col_name: name of the value column being analyzed
        - var_x: row identifier (category)
        - One column per var_y with correlation values

    Raises
    ------
    UnitError
        If value_col lacks unit metadata and allow_missing_units=False.
    ConfigurationError
        If correlation_type is not CorrelationOperation.PEARSON or CorrelationOperation.SPEARMAN.
    DataValidationError
        If value_col is not numeric.

    Notes
    -----
    - QC filtering: Excludes INVALID and OUTLIER flags; treats BELOW_DL as missing
    - Pair ordering: Returns only unique ordered pairs (var_x <= var_y) plus diagonal
    - For N categories, returns N*(N+1)/2 pairs per group
    - Diagonal (self-correlation) always equals 1.0 (or NaN if constant)
    - NaN values: Returned if insufficient variance or data

    Examples
    --------
    >>> import pandas as pd
    >>> from air_quality.dataset.time_series import TimeSeriesDataset
    >>> from air_quality.analysis.correlation import compute_pairwise
    >>> from air_quality.qc_flags import QCFlag
    >>>
    >>> df = pd.DataFrame({
    ...     "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
    ...     "site_id": ["site1"] * 10,
    ...     "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
    ...     "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
    ...     "flag": [QCFlag.VALID.value] * 10,
    ... })
    >>> dataset = TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ug/m3"})
    >>> result = compute_pairwise(dataset, group_by=None, correlation_type=CorrelationOperation.PEARSON)
    >>> result  # 3 pairs: (PM10, PM10), (PM10, PM25), (PM25, PM25)
    """
    from ...dataset.time_series import TimeSeriesDataset
    from ...exceptions import ConfigurationError, UnitError
    from ...qc_flags import filter_by_qc_flags, mark_missing_by_flags

    # Validate correlation_type
    if correlation_type not in (
        CorrelationOperation.PEARSON,
        CorrelationOperation.SPEARMAN,
    ):
        raise ConfigurationError(
            f"Unsupported correlation method: {correlation_type}. "
            f"Expected 'CorrelationOperation.PEARSON' or 'CorrelationOperation.SPEARMAN'."
        )

    # Normalize value_cols to list
    if isinstance(value_cols, str):
        value_cols_list = [value_cols]
    else:
        value_cols_list = value_cols

    # Process each value column
    all_results = []

    for value_col in value_cols_list:
        # Check unit presence (unless overridden)
        if not allow_missing_units:
            if dataset.column_units is None or value_col not in dataset.column_units:
                raise UnitError(
                    f"Missing unit metadata for column '{value_col}'. "
                    f"Correlation requires units for interpretability. "
                    f"Set allow_missing_units=True to override (not recommended)."
                )

        # Get Polars LazyFrame
        lf = dataset.lazyframe

        # Apply QC filtering (exclude INVALID, OUTLIER)
        lf_filtered = filter_by_qc_flags(lf, flag_col=flag_col)

        # Mark BELOW_DL as missing (set value to null)
        lf_filtered = mark_missing_by_flags(
            lf_filtered, conc_col=value_col, flag_col=flag_col
        )

        # Collect for pivot operations (required by pivot)
        df_clean = lf_filtered.collect()

        # Drop rows with null values in category_col or value_col
        df_clean = df_clean.filter(
            pl.col(category_col).is_not_null() & pl.col(value_col).is_not_null()
        )

        # Filter by min_samples per category per group
        group_cols = group_by if group_by else []
        count_expr = [*group_cols, category_col]

        # Count valid observations per category per group
        counts = (
            df_clean.group_by(count_expr)
            .agg(pl.len().alias("n_obs"))
            .filter(pl.col("n_obs") >= min_samples)
        )

        # Inner join to keep only categories with sufficient samples
        df_sufficient = df_clean.join(
            counts.select([*count_expr]),
            on=count_expr,
            how="inner",
        )

        # Get list of unique categories
        unique_categories = (
            df_sufficient.select(pl.col(category_col)).unique().to_series().to_list()
        )
        unique_categories_sorted = sorted(unique_categories)

        # Generate ordered pairs (var_x <= var_y)
        pairs = generate_ordered_pairs(unique_categories_sorted)

        # Compute correlations
        if group_cols:
            # Grouped correlation
            results = []
            for group_vals, group_df in df_clean.group_by(group_cols):
                group_corrs = compute_correlations_for_group(
                    group_df,
                    category_col,
                    value_col,
                    pairs,
                    correlation_type,
                    group_vals,
                    group_cols,
                )
                results.extend(group_corrs)

            if not results:
                result_df_for_col = pl.DataFrame(
                    {
                        **{col: [] for col in group_cols},
                        "var_x": [],
                        "var_y": [],
                        "correlation": [],
                        "n": [],
                    }
                )
            else:
                result_df_for_col = pl.DataFrame(results)
        else:
            # Global correlation
            results = compute_correlations_for_group(
                df_clean, category_col, value_col, pairs, correlation_type, None, []
            )
            if not results:
                result_df_for_col = pl.DataFrame(
                    {
                        "var_x": [],
                        "var_y": [],
                        "correlation": [],
                        "n": [],
                    }
                )
            else:
                result_df_for_col = pl.DataFrame(results)

        # Add value_col_name column to track which column this is
        result_df_for_col = result_df_for_col.with_columns(
            pl.lit(value_col).alias("value_col_name")
        )

        # Append to results list
        all_results.append(result_df_for_col)

    # Concatenate all results (one per value column)
    if len(all_results) == 0:
        # No results at all - return empty dataframe
        group_cols = group_by if group_by else []
        if group_cols:
            final_result = pl.DataFrame(
                {
                    **{col: [] for col in group_cols},
                    "value_col_name": [],
                    "var_x": [],
                    "var_y": [],
                    "correlation": [],
                    "n": [],
                }
            )
        else:
            final_result = pl.DataFrame(
                {
                    "value_col_name": [],
                    "var_x": [],
                    "var_y": [],
                    "correlation": [],
                    "n": [],
                }
            )
    elif len(all_results) == 1:
        final_result = all_results[0]
    else:
        final_result = pl.concat(all_results, how="vertical")

    # Convert to wide format if requested
    if output_format == OutputFormat.WIDE:
        # Pivot: var_y becomes columns, var_x stays as rows
        index_cols = []
        if group_by:
            index_cols.extend(group_by)
        index_cols.extend(["value_col_name", "var_x"])

        final_result = final_result.pivot(
            index=index_cols,
            on="var_y",
            values="correlation",
        )

    return final_result


__all__ = ["compute_pairwise"]
