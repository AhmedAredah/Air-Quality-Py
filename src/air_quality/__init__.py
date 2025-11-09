"""air_quality package init.

Exposes package version and minimal convenience symbols.
Feature 002: Units & Time Primitives - Public API exports (Phase 9).
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .module import DashboardPayload

__version__ = "0.1.0"


def hello() -> str:
    return "Hello from air-quality!"


# Feature 002: Units & Time Primitives - Public API (implemented Phase 9)
from .units import (
    Unit,
    can_convert,
    convert_values,
    get_factor,
    round_for_reporting,
    validate_units_schema,
)
from .time_utils import (
    TimeBounds,
    compute_time_bounds,
    ensure_timezone_aware,
    resample_mean,
    rolling_window_mean,
    to_utc,
)

__all__ = [
    # Core package
    "__version__",
    "hello",
    # Feature 002: Units (6 exports)
    "Unit",
    "can_convert",
    "convert_values",
    "get_factor",
    "round_for_reporting",
    "validate_units_schema",
    # Feature 002: Time utilities (6 exports)
    "TimeBounds",
    "compute_time_bounds",
    "ensure_timezone_aware",
    "resample_mean",
    "rolling_window_mean",
    "to_utc",
]

# DashboardPayload is available for type hints via:
# from air_quality.module import DashboardPayload
