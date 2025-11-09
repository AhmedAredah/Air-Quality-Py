"""air_quality.stats_analysis.core.constants

Constants for statistical analysis modules.

Constitution compliance:
- Section 3: Time unit standards (hour, day, calendar_month, calendar_year)
- Section 7: Default configuration values
"""

from __future__ import annotations

from typing import Literal


# Time units for trend analysis (calendar-aware semantics per Spec clarifications)
ALLOWED_TIME_UNITS: set[Literal["hour", "day", "calendar_month", "calendar_year"]] = {
    "hour",
    "day",
    "calendar_month",
    "calendar_year",
}

# Default thresholds for statistical computations
DEFAULT_MIN_SAMPLES: int = 3
"""Minimum number of valid observations for correlation and trend analysis."""

DEFAULT_MIN_DURATION_YEARS: float = 1.0
"""Minimum duration in years for trend analysis (flagged if shorter)."""

# Quantile levels for descriptive statistics
DEFAULT_QUANTILES: tuple[float, ...] = (0.05, 0.25, 0.75, 0.95)
"""Default quantile levels: 5th, 25th, 75th, 95th percentiles."""

# QC flag sets (Constitution Sec. 3)
EXCLUDE_FLAGS: set[str] = {"invalid", "outlier"}
"""QC flags to exclude entirely from statistical computations."""

MISSING_FLAGS: set[str] = {"below_dl"}
"""QC flags treated as missing values (included in count but not in mean/correlation)."""

# Statistics computed by descriptive module
DESCRIPTIVE_STATS: tuple[str, ...] = (
    "mean",
    "median",
    "std",
    "min",
    "max",
    "q05",
    "q25",
    "q75",
    "q95",
)
"""Standard statistics computed for descriptive summaries."""

# Correlation methods
CORRELATION_METHODS: set[Literal["pearson", "spearman"]] = {"pearson", "spearman"}
"""Supported correlation methods."""
