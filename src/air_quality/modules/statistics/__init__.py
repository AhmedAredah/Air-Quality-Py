"""air_quality.modules.statistics

Statistical analysis modules for air quality data.

This package provides:
- DescriptiveStatsModule: Descriptive statistics per pollutant/group
- CorrelationModule: Pairwise correlations (Pearson/Spearman)
- TrendModule: Linear trends with calendar-aware time units

Each module includes its configuration enums inline.

Constitution compliance:
- Section 7: Modules inherit AirQualityModule
- Section 8: Dual reporting (dashboard + CLI)
- Section 15: Provenance attachment
"""

from .descriptive import DescriptiveStatsModule
from .correlation import CorrelationModule
from .trend import TrendModule

__all__ = [
    "DescriptiveStatsModule",
    "CorrelationModule",
    "TrendModule",
]
