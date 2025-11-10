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
from ...mapping import ColumnMappingResult
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


class TrendModuleName(Enum):
    """Module name identifier for trend module."""

    VALUE = "trend"


class TrendSchemaVersion(Enum):
    """Output schema version for trend module."""

    V1_0_0 = "1.0.0"


class TrendModule(AirQualityModule):
    """Placeholder module for trend analysis (Phase 5).

    To be implemented in T054-T059.
    """

    MODULE_NAME = TrendModuleName.VALUE
    DOMAIN = ModuleDomain.STATISTICS
    OUTPUT_SCHEMA_VERSION = TrendSchemaVersion.V1_0_0

    ConfigKey = TrendConfig

    @classmethod
    def _get_required_columns_static(cls) -> Dict[str, list[str]]:
        """Return required columns."""
        return {}

    @classmethod
    def _dataset_from_mapped_df_static(
        cls,
        mapping_result: ColumnMappingResult,
        metadata: Dict[str, Any],
    ) -> BaseDataset:
        """Construct dataset from mapping result."""
        raise NotImplementedError("TrendModule not yet implemented (Phase 5)")

    def _run_impl(self, operations: Optional[Sequence[Enum]] = None) -> None:
        """Execute trend analysis."""
        raise NotImplementedError("TrendModule not yet implemented (Phase 5)")

    def _build_dashboard_report_impl(self) -> Dict[str, Any]:
        """Build dashboard metrics."""
        raise NotImplementedError("TrendModule not yet implemented (Phase 5)")

    def _build_cli_report_impl(self) -> str:
        """Build CLI report content."""
        raise NotImplementedError("TrendModule not yet implemented (Phase 5)")

    def _validate_config_impl(self) -> None:
        """Validate configuration."""
        pass  # No validation for placeholder
