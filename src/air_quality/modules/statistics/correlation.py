"""air_quality.modules.statistics.correlation

CorrelationModule: pairwise correlations (Pearson/Spearman) with ordered unique pairs.

Constitution compliance:
- Section 7: Inherits AirQualityModule, implements required hooks
- Section 8: Dual reporting (dashboard + CLI)
- Section 15: Units provenance (units_status, missing list on override)
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional, Sequence

from ...dataset.base import BaseDataset
from ...module import AirQualityModule, ModuleDomain


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


# Placeholder for T040, T041, T042, T043
