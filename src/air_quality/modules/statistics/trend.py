"""air_quality.modules.statistics.trend

TrendModule: linear trends (conc ~ time) with calendar-aware time units.

Constitution compliance:
- Section 7: Inherits AirQualityModule, implements required hooks
- Section 8: Dual reporting (dashboard + CLI)
- Section 15: Provenance (time bounds, duration, thresholds)
- Section 3: Calendar-aware time_unit semantics
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional, Sequence

from ...dataset.base import BaseDataset
from ...module import AirQualityModule, ModuleDomain


class TrendConfig(str, Enum):
    """Configuration keys for linear trend analysis module.

    Constitution References
    -----------------------
    - Section 7: Module configuration standards
    - Section 15: Units enforcement (required for trends)

    Attributes
    ----------
    TIME_UNIT : str
        Time unit for slope computation (calendar-aware semantics).
    GROUP_BY : str
        Grouping columns (None for global aggregation).
    MIN_SAMPLES : str
        Minimum number of valid observations for trend.
    MIN_DURATION_YEARS : str
        Minimum duration in years (flagged if shorter).
    POLLUTANT_COL : str
        Pollutant identifier column name.
    CONC_COL : str
        Concentration value column name.
    FLAG_COL : str
        QC flag column name.
    DATETIME_COL : str
        Datetime column name for time index.
    """

    TIME_UNIT = "time_unit"
    GROUP_BY = "group_by"
    MIN_SAMPLES = "min_samples"
    MIN_DURATION_YEARS = "min_duration_years"
    POLLUTANT_COL = "pollutant_col"
    CONC_COL = "conc_col"
    FLAG_COL = "flag_col"
    DATETIME_COL = "datetime_col"


# Placeholder for T054, T055, T056, T057
