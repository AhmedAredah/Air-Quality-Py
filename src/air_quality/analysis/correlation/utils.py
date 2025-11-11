"""Utility functions for correlation analysis."""

from __future__ import annotations

from typing import Any

from .enums import CorrelationOperation
from .pearson import compute_pearson
from .spearman import compute_spearman


def generate_ordered_pairs(categories: list[str]) -> list[tuple[str, str]]:
    """Generate ordered unique pairs (var_x <= var_y) including diagonal.

    Parameters
    ----------
    categories : list[str]
        List of category names (sorted).

    Returns
    -------
    list[tuple[str, str]]
        List of (var_x, var_y) pairs where var_x <= var_y.

    Examples
    --------
    >>> generate_ordered_pairs(["CO", "NO2", "O3"])
    [('CO', 'CO'), ('CO', 'NO2'), ('CO', 'O3'), ('NO2', 'NO2'), ('NO2', 'O3'), ('O3', 'O3')]
    """
    pairs = []
    for i, var_x in enumerate(categories):
        for var_y in categories[i:]:  # Start from i to ensure var_x <= var_y
            pairs.append((var_x, var_y))
    return pairs


def compute_correlations_for_group(
    group_df: "polars.DataFrame",  # type: ignore[name-defined]  # noqa: F821
    category_col: str,
    value_col: str,
    pairs: list[tuple[str, str]],
    correlation_type: CorrelationOperation,
    group_vals: tuple[Any, ...] | None,
    group_cols: list[str],
) -> list[dict[str, Any]]:
    """Compute correlations for a single group using simple aggregation.

    Collects all observations per category and computes pairwise correlations.
    No timestamp alignment required - treats all observations as independent samples.

    Parameters
    ----------
    group_df : polars.DataFrame
        Data for this group (long format).
    category_col : str
        Column identifying categories.
    value_col : str
        Column containing values.
    pairs : list[tuple[str, str]]
        List of (var_x, var_y) pairs to compute.
    correlation_type : CorrelationOperation
        Correlation method: PEARSON or SPEARMAN.
    group_vals : tuple | None
        Group identifier values (None for global).
    group_cols : list[str]
        Group column names.

    Returns
    -------
    list[dict]
        List of correlation results for this group.
    """
    import polars as pl
    import numpy as np

    results = []

    # Collect observations per category
    category_data = {}
    for category_name in (
        group_df.select(pl.col(category_col)).unique().to_series().to_list()
    ):
        cat_vals = (
            group_df.filter(pl.col(category_col) == category_name)
            .select(pl.col(value_col))
            .to_numpy()
            .flatten()
        )
        # Drop NaNs
        cat_vals_clean = cat_vals[~np.isnan(cat_vals)]
        category_data[category_name] = cat_vals_clean

    # Compute correlations for each pair
    for var_x, var_y in pairs:
        # Skip if categories don't exist
        if var_x not in category_data or var_y not in category_data:
            continue

        x_vals = category_data[var_x]
        y_vals = category_data[var_y]

        # Use minimum length for pairing (simple approach)
        n = min(len(x_vals), len(y_vals))

        if n == 0:
            correlation = np.nan
        else:
            # Truncate to same length
            x_paired = x_vals[:n]
            y_paired = y_vals[:n]

            if correlation_type == CorrelationOperation.PEARSON:
                correlation = compute_pearson(x_paired, y_paired)
            elif correlation_type == CorrelationOperation.SPEARMAN:
                correlation = compute_spearman(x_paired, y_paired)
            else:
                correlation = np.nan

        # Build result dict
        result = {}
        if group_vals is not None:
            if isinstance(group_vals, tuple):
                for col, val in zip(group_cols, group_vals):
                    result[col] = val
            else:
                # Single group column
                result[group_cols[0]] = group_vals

        result["var_x"] = var_x
        result["var_y"] = var_y
        result["correlation"] = correlation
        result["n"] = n

        results.append(result)

    return results


__all__ = ["generate_ordered_pairs", "compute_correlations_for_group"]
