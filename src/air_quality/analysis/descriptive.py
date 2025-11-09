"""air_quality.stats_analysis.core.descriptive

Descriptive statistics primitives (mean, median, std, quantiles, counts).

Constitution compliance:
- Section 11: Columnar groupby/agg (Polars), no Python loops
- Section 5: QC flag filtering (exclude invalid/outlier, treat below_dl as missing)
"""

from __future__ import annotations

from .constants import DEFAULT_QUANTILES


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


# Placeholder for T023, T024: compute_descriptives implementation
