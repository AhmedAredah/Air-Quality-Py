"""air_quality.stats_analysis.configs

Configuration enums for statistical analysis modules.

Constitution compliance:
- Section 7: Module configuration validation
- Section 15: Units and provenance requirements
"""

from __future__ import annotations

from enum import Enum

from ..units import TimeUnit
from .core.constants import CorrelationMethod


class DescriptiveStatsConfig(str, Enum):
    """Configuration keys for descriptive statistics module.

    Constitution References
    -----------------------
    - Section 7: Module configuration standards

    Attributes
    ----------
    GROUP_BY : str
        Grouping columns (None for global aggregation).
    QUANTILES : str
        Quantile levels to compute.
    POLLUTANT_COL : str
        Pollutant identifier column name.
    CONC_COL : str
        Concentration value column name.
    FLAG_COL : str
        QC flag column name.
    """

    GROUP_BY = "group_by"
    QUANTILES = "quantiles"
    POLLUTANT_COL = "pollutant_col"
    CONC_COL = "conc_col"
    FLAG_COL = "flag_col"


class CorrelationConfig(str, Enum):
    """Configuration keys for correlation analysis module.

    Constitution References
    -----------------------
    - Section 7: Module configuration standards
    - Section 15: Units enforcement policy

    Attributes
    ----------
    METHOD : str
        Correlation method (PEARSON or SPEARMAN).
    GROUP_BY : str
        Grouping columns (None for global aggregation).
    MIN_SAMPLES : str
        Minimum number of valid pairwise observations.
    ALLOW_MISSING_UNITS : str
        Whether to allow correlation with missing unit metadata.
    POLLUTANT_COL : str
        Pollutant identifier column name.
    CONC_COL : str
        Concentration value column name.
    FLAG_COL : str
        QC flag column name.
    """

    METHOD = "method"
    GROUP_BY = "group_by"
    MIN_SAMPLES = "min_samples"
    ALLOW_MISSING_UNITS = "allow_missing_units"
    POLLUTANT_COL = "pollutant_col"
    CONC_COL = "conc_col"
    FLAG_COL = "flag_col"


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


__all__ = [
    "DescriptiveStatsConfig",
    "CorrelationConfig",
    "TrendConfig",
]
