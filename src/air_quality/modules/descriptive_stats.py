"""air_quality.modules.descriptive_stats

DescriptiveStatsModule: descriptive statistics per pollutant and grouping keys.

Constitution compliance:
- Section 7: Inherits AirQualityModule, implements required hooks
- Section 8: Dual reporting (dashboard + CLI)
- Section 15: Provenance attachment
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional, Sequence

from ..dataset.base import BaseDataset
from ..module import AirQualityModule, ModuleDomain

# Placeholder for T026, T027, T028, T029
