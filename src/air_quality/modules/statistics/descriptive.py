"""air_quality.modules.statistics.descriptive

DescriptiveStatsModule: descriptive statistics per pollutant and grouping keys.

Constitution compliance:
- Section 7: Inherits AirQualityModule, implements required hooks
- Section 8: Dual reporting (dashboard + CLI)
- Section 15: Provenance attachment
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional, Sequence

from ...dataset.base import BaseDataset
from ...module import AirQualityModule, ModuleDomain


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


# Placeholder for T026, T027, T028, T029
