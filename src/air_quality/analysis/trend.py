"""air_quality.analysis.trend

Linear trend primitives (conc ~ time) with calendar-aware time units.

Constitution compliance:
- Section 11: Closed-form OLS via sufficient statistics
- Section 15: Unit enforcement for slopes (Unit per time_unit)
- Section 3: Calendar-aware time semantics (hour/day/calendar_month/calendar_year)
"""

from __future__ import annotations

from ..units import TimeUnit


# Default thresholds for trend analysis
DEFAULT_MIN_SAMPLES: int = 3
"""Minimum number of valid observations for trend analysis."""

DEFAULT_MIN_DURATION_YEARS: float = 1.0
"""Minimum duration in years for trend analysis (flagged if shorter)."""

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


__all__ = [
    "TimeUnit",
    "DEFAULT_MIN_SAMPLES",
    "DEFAULT_MIN_DURATION_YEARS",
    "ALLOWED_TIME_UNITS",
]


# Placeholder for T051, T052, T053
