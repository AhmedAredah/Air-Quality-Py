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


# Placeholder for T023, T024: compute_descriptives implementation
