"""air_quality.analysis

Statistical analysis primitives and utilities.

This package provides computational primitives for:
- Descriptive statistics (mean, median, quantiles, counts)
- Correlation analysis (Pearson, Spearman)
- Trend analysis (linear OLS, calendar-aware time units)

Constitution compliance:
- Section 11: Columnar/vectorized operations (Polars/Pandas)
- Section 15: Units and provenance support
"""

# Maintain backward compatibility with old imports
from .correlation import (
    CorrelationOperation,
    OutputFormat as CorrelationOutputFormat,
    compute_pairwise,
)
from .correlation import DEFAULT_MIN_SAMPLES as CORRELATION_DEFAULT_MIN_SAMPLES
from .descriptive import (
    DescriptiveStatsOperation,
    OutputFormat as DescriptiveOutputFormat,
    compute_descriptives,
)
from .trend import (
    ALLOWED_TIME_UNITS,
    DEFAULT_MIN_DURATION_YEARS,
    TimeUnit,
    TrendOperation,
    compute_linear_trend,
)
from .trend import DEFAULT_MIN_SAMPLES as TREND_DEFAULT_MIN_SAMPLES

__all__ = [
    # Correlation
    "compute_pairwise",
    "CorrelationOperation",
    "CorrelationOutputFormat",
    "CORRELATION_DEFAULT_MIN_SAMPLES",
    # Descriptive
    "compute_descriptives",
    "DescriptiveStatsOperation",
    "DescriptiveOutputFormat",
    # Trend
    "compute_linear_trend",
    "TrendOperation",
    "TimeUnit",
    "TREND_DEFAULT_MIN_SAMPLES",
    "DEFAULT_MIN_DURATION_YEARS",
    "ALLOWED_TIME_UNITS",
]
