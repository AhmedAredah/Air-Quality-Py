"""Constants for trend analysis."""

from ...units import TimeUnit

# Default thresholds for trend analysis
DEFAULT_MIN_SAMPLES: int = 3
"""Minimum number of valid observations for trend analysis."""

DEFAULT_MIN_DURATION_YEARS: float = 1.0
"""Minimum duration in years for trend analysis (flagged if shorter)."""

# Time units for validation
ALLOWED_TIME_UNITS: frozenset[TimeUnit] = frozenset(
    {
        TimeUnit.HOUR,
        TimeUnit.DAY,
        TimeUnit.CALENDAR_MONTH,
        TimeUnit.CALENDAR_YEAR,
    }
)
"""Allowed time units for trend analysis."""


__all__ = [
    "DEFAULT_MIN_SAMPLES",
    "DEFAULT_MIN_DURATION_YEARS",
    "ALLOWED_TIME_UNITS",
]
