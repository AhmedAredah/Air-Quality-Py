"""air_quality.modules.correlation

CorrelationModule: pairwise correlations (Pearson/Spearman) with ordered unique pairs.

Constitution compliance:
- Section 7: Inherits AirQualityModule, implements required hooks
- Section 8: Dual reporting (dashboard + CLI)
- Section 15: Units provenance (units_status, missing list on override)
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional, Sequence

from ..dataset.base import BaseDataset
from ..module import AirQualityModule, ModuleDomain

# Placeholder for T040, T041, T042, T043
