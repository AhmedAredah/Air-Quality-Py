"""air_quality.analysis.trend

Linear trend primitives (conc ~ time) with calendar-aware time units.

Constitution compliance:
- Section 11: Closed-form OLS via sufficient statistics
- Section 15: Unit enforcement for slopes
- Section 3: Calendar-aware time semantics
"""

from ...units import TimeUnit
from .constants import (
    ALLOWED_TIME_UNITS,
    DEFAULT_MIN_DURATION_YEARS,
    DEFAULT_MIN_SAMPLES,
)
from .core import compute_linear_trend
from .enums import TrendOperation

__all__ = [
    "compute_linear_trend",
    "TrendOperation",
    "TimeUnit",
    "DEFAULT_MIN_SAMPLES",
    "DEFAULT_MIN_DURATION_YEARS",
    "ALLOWED_TIME_UNITS",
]
