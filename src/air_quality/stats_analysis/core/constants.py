"""air_quality.stats_analysis.core.constants

Constants for statistical analysis modules.

Constitution compliance:
- Section 7: Default configuration values
- Section 8: Module-specific enums and settings

Note: TimeUnit is defined in air_quality.units (shared across library)
"""

from __future__ import annotations

from enum import Enum

from ....units import TimeUnit


class CorrelationMethod(str, Enum):
    """Correlation computation methods.

    Constitution References
    -----------------------
    - Section 7: Module configuration standards

    Methods:
    - PEARSON: Linear correlation (parametric)
    - SPEARMAN: Rank correlation (non-parametric)
    """

    PEARSON = "pearson"
    SPEARMAN = "spearman"


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


# Default thresholds for statistical computations
DEFAULT_MIN_SAMPLES: int = 3
"""Minimum number of valid observations for correlation and trend analysis."""

DEFAULT_MIN_DURATION_YEARS: float = 1.0
"""Minimum duration in years for trend analysis (flagged if shorter)."""

# Quantile levels for descriptive statistics
DEFAULT_QUANTILES: tuple[float, ...] = (0.05, 0.25, 0.75, 0.95)
"""Default quantile levels: 5th, 25th, 75th, 95th percentiles."""

# Time units for validation (imported from main units module)
ALLOWED_TIME_UNITS: frozenset[TimeUnit] = frozenset(
    {
        TimeUnit.HOUR,
        TimeUnit.DAY,
        TimeUnit.CALENDAR_MONTH,
        TimeUnit.CALENDAR_YEAR,
    }
)
"""Allowed time units for trend analysis."""

# Correlation methods for validation
ALLOWED_CORRELATION_METHODS: frozenset[CorrelationMethod] = frozenset(
    {
        CorrelationMethod.PEARSON,
        CorrelationMethod.SPEARMAN,
    }
)
"""Allowed correlation methods."""

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

# Re-export commonly used items for convenience
__all__ = [
    "CorrelationMethod",
    "StatisticType",
    "TimeUnit",
    "DEFAULT_MIN_SAMPLES",
    "DEFAULT_MIN_DURATION_YEARS",
    "DEFAULT_QUANTILES",
    "ALLOWED_TIME_UNITS",
    "ALLOWED_CORRELATION_METHODS",
    "DESCRIPTIVE_STATS",
]
