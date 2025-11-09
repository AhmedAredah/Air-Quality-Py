"""air_quality.stats_analysis.configs

Configuration dataclasses for statistical analysis modules.

Constitution compliance:
- Section 7: Module configuration validation
- Section 15: Units and provenance requirements
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..units import TimeUnit
from .core.constants import CorrelationMethod


@dataclass(frozen=True, slots=True)
class DescriptiveStatsConfig:
    """Configuration for descriptive statistics module.

    Constitution References
    -----------------------
    - Section 7: Module configuration standards

    Attributes
    ----------
    group_by : list[str] | None
        Grouping columns (None for global aggregation).
    quantiles : tuple[float, ...], default=(0.05, 0.25, 0.75, 0.95)
        Quantile levels to compute.
    pollutant_col : str, default='pollutant'
        Pollutant identifier column name.
    conc_col : str, default='conc'
        Concentration value column name.
    flag_col : str, default='flag'
        QC flag column name.
    """

    group_by: Optional[list[str]] = None
    quantiles: tuple[float, ...] = (0.05, 0.25, 0.75, 0.95)
    pollutant_col: str = "pollutant"
    conc_col: str = "conc"
    flag_col: str = "flag"


@dataclass(frozen=True, slots=True)
class CorrelationConfig:
    """Configuration for correlation analysis module.

    Constitution References
    -----------------------
    - Section 7: Module configuration standards
    - Section 15: Units enforcement policy

    Attributes
    ----------
    group_by : list[str] | None
        Grouping columns (None for global aggregation).
    method : CorrelationMethod, default=CorrelationMethod.PEARSON
        Correlation method (PEARSON or SPEARMAN).
    min_samples : int, default=3
        Minimum number of valid pairwise observations.
    allow_missing_units : bool, default=False
        Whether to allow correlation with missing unit metadata.
        If False, raises UnitError for pollutants without units.
        If True, proceeds and records override in provenance.
    pollutant_col : str, default='pollutant'
        Pollutant identifier column name.
    conc_col : str, default='conc'
        Concentration value column name.
    flag_col : str, default='flag'
        QC flag column name.
    """

    method: CorrelationMethod = CorrelationMethod.PEARSON
    group_by: Optional[list[str]] = None
    min_samples: int = 3
    allow_missing_units: bool = False
    pollutant_col: str = "pollutant"
    conc_col: str = "conc"
    flag_col: str = "flag"


@dataclass(frozen=True, slots=True)
class TrendConfig:
    """Configuration for linear trend analysis module.

    Constitution References
    -----------------------
    - Section 7: Module configuration standards
    - Section 15: Units enforcement (required for trends)

    Attributes
    ----------
    time_unit : TimeUnit
        Time unit for slope computation (calendar-aware semantics).
        One of: TimeUnit.HOUR, TimeUnit.DAY, TimeUnit.CALENDAR_MONTH, TimeUnit.CALENDAR_YEAR.
    group_by : list[str] | None
        Grouping columns (None for global aggregation).
    min_samples : int, default=3
        Minimum number of valid observations for trend.
    min_duration_years : float, default=1.0
        Minimum duration in years (flagged if shorter).
    pollutant_col : str, default='pollutant'
        Pollutant identifier column name.
    conc_col : str, default='conc'
        Concentration value column name.
    flag_col : str, default='flag'
        QC flag column name.
    datetime_col : str, default='datetime'
        Datetime column name for time index.
    """

    time_unit: TimeUnit
    group_by: Optional[list[str]] = None
    min_samples: int = 3
    min_duration_years: float = 1.0
    pollutant_col: str = "pollutant"
    conc_col: str = "conc"
    flag_col: str = "flag"
    datetime_col: str = "datetime"
