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

import polars as pl

from ...analysis.trend import compute_linear_trend, TrendOperation
from ...dataset.base import BaseDataset
from ...dataset.time_series import TimeSeriesDataset
from ...mapping import ColumnMappingResult
from ...module import AirQualityModule, ModuleDomain
from ...time_utils import compute_time_bounds
from ...units import TimeUnit


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
    CATEGORY_COL : str
        Category identifier column name (e.g., pollutant).
    VALUE_COL : str
        Numeric value column name to analyze.
    FLAG_COL : str
        QC flag column name.
    DATETIME_COL : str
        Datetime column name for time index.
    ALLOW_MISSING_UNITS : str
        Whether to allow trends with missing unit metadata.
    """

    TIME_UNIT = "time_unit"
    GROUP_BY = "group_by"
    MIN_SAMPLES = "min_samples"
    MIN_DURATION_YEARS = "min_duration_years"
    CATEGORY_COL = "category_col"
    VALUE_COL = "value_col"
    FLAG_COL = "flag_col"
    DATETIME_COL = "datetime_col"
    ALLOW_MISSING_UNITS = "allow_missing_units"


class TrendResult(Enum):
    """Result keys for TrendModule.

    Attributes
    ----------
    TRENDS : str
        DataFrame with trend results (slope, intercept, R²).
    TIME_BOUNDS : str
        Time range of the dataset (start, end).
    TIME_UNIT : str
        Time unit used for trend computation.
    N_TRENDS : str
        Number of trends computed.
    CONFIG : str
        Configuration used for computation.
    """

    TRENDS = "trends"
    TIME_BOUNDS = "time_bounds"
    TIME_UNIT = "time_unit"
    N_TRENDS = "n_trends"
    CONFIG = "config"


class TrendModuleName(Enum):
    """Module name identifier for trend module."""

    VALUE = "trend"


class TrendSchemaVersion(Enum):
    """Output schema version for trend module."""

    V1_0_0 = "1.0.0"


class TrendModule(AirQualityModule):
    """Module for computing linear trends over time.

    This module provides linear trend analysis including:
    - Closed-form OLS regression (slope, intercept, R²)
    - Calendar-aware time conversion (hour, day, calendar_month, calendar_year)
    - Duration calculation and flagging (short_duration_flag, low_n_flag)
    - Unit enforcement (slope_units = conc_unit/time_unit)
    - Optional grouping by site_id or other dimensions
    - QC-aware filtering

    Operations
    ----------
    - LINEAR_TREND: Compute linear trends for all pollutants

    Constitution compliance:
    - Section 7: Inherits AirQualityModule, implements required hooks
    - Section 8: Dual reporting (dashboard + CLI)
    - Section 11: Uses Polars vectorized operations
    - Section 15: Provenance attachment with time bounds and duration

    Examples
    --------
    >>> import pandas as pd
    >>> from air_quality.modules.statistics.trend import (
    ...     TrendModule,
    ...     TrendOperation,
    ...     TrendResult
    ... )
    >>> from air_quality.units import TimeUnit
    >>> from air_quality.qc_flags import QCFlag
    >>> from air_quality.dataset.time_series import TimeSeriesDataset
    >>> df = pd.DataFrame({
    ...     'datetime': pd.date_range('2024-01-01', periods=100, freq='D'),
    ...     'site_id': ['site1'] * 100,
    ...     'pollutant': ['PM25'] * 100,
    ...     'conc': [2.0 * i + 5.0 for i in range(100)],
    ...     'flag': [QCFlag.VALID.value] * 100
    ... })
    >>> dataset = TimeSeriesDataset.from_dataframe(df, column_units={'conc': 'ug/m3'})
    >>> module = TrendModule(
    ...     dataset=dataset,
    ...     config={
    ...         'time_unit': TimeUnit.DAY,
    ...         'category_col': 'pollutant',
    ...         'value_col': 'conc'
    ...     }
    ... )
    >>> module.run()
    >>> trends = module.get_result(TrendResult.TRENDS)
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
        raise NotImplementedError(
            "TrendModule._dataset_from_mapped_df_static not yet implemented"
        )

    def _run_impl(self, operations: Optional[Sequence[Enum]] = None) -> None:
        """Execute trend analysis.

        Parameters
        ----------
        operations : Sequence[TrendOperation], optional
            Specific operations to run. If None, runs all operations.
            Currently only LINEAR_TREND is available.
        """
        # Determine which operations to run
        if operations is None:
            # Run all operations by default
            ops_to_run = list(TrendOperation)
        else:
            # Cast to list of TrendOperation for type safety
            ops_to_run = [TrendOperation(op) for op in operations]

        self.logger.info(f"Running operations: {[op.value for op in ops_to_run]}")

        # Execute requested operations
        for op in ops_to_run:
            if op == TrendOperation.LINEAR_TREND:
                self._compute_trends()
            else:
                self.logger.warning(f"Unknown operation: {op}")

    def _compute_trends(self) -> None:
        """Compute linear trends with QC-aware filtering and unit enforcement."""
        self.logger.info("Computing linear trends")

        # Extract configuration
        time_unit = self.config.get(TrendConfig.TIME_UNIT, TimeUnit.DAY)
        group_by = self.config.get(TrendConfig.GROUP_BY, None)
        min_samples = self.config.get(TrendConfig.MIN_SAMPLES, 3)
        min_duration_years = self.config.get(TrendConfig.MIN_DURATION_YEARS, 1.0)
        allow_missing_units = self.config.get(TrendConfig.ALLOW_MISSING_UNITS, False)
        category_col = self.config.get(TrendConfig.CATEGORY_COL, "pollutant")
        value_col = self.config.get(TrendConfig.VALUE_COL, "concentration")
        flag_col = self.config.get(TrendConfig.FLAG_COL, "flag")
        datetime_col = self.config.get(TrendConfig.DATETIME_COL, "datetime")

        # Ensure time_unit is TimeUnit enum
        if isinstance(time_unit, str):
            time_unit = TimeUnit(time_unit)

        # Ensure dataset is TimeSeriesDataset for unit access
        assert isinstance(self.dataset, TimeSeriesDataset)

        # Compute trends
        trends_df = compute_linear_trend(
            dataset=self.dataset,
            time_unit=time_unit,
            group_by=group_by,
            category_col=category_col,
            datetime_col=datetime_col,
            value_col=value_col,
            flag_col=flag_col,
            min_samples=min_samples,
            min_duration_years=min_duration_years,
            allow_missing_units=allow_missing_units,
        )

        # Store results
        self.results[TrendResult.TRENDS] = trends_df
        self.results[TrendResult.TIME_UNIT] = time_unit.value
        self.results[TrendResult.N_TRENDS] = len(trends_df)
        self.results[TrendResult.CONFIG] = {
            "time_unit": time_unit.value,
            "group_by": group_by,
            "min_samples": min_samples,
            "min_duration_years": min_duration_years,
            "allow_missing_units": allow_missing_units,
        }

        # Compute time bounds for provenance
        time_bounds = compute_time_bounds(
            self.dataset.lazyframe,
            time_col=datetime_col,
        )
        self.results[TrendResult.TIME_BOUNDS] = time_bounds

        self.logger.info(
            f"Computed {len(trends_df)} trends using time unit {time_unit.value}"
        )

    def _build_dashboard_report_impl(self) -> Dict[str, Any]:
        """Build dashboard metrics.

        Returns
        -------
        dict
            Metrics including trend results, time unit, and configuration.

        Constitution References
        -----------------------
        - Section 8: Dashboard reporting format
        - Section 15: Time bounds and duration in dashboard output
        """
        trends_df = self.results[TrendResult.TRENDS]
        time_bounds = self.results[TrendResult.TIME_BOUNDS]
        config = self.results[TrendResult.CONFIG]

        # Convert to dict for JSON serialization
        return {
            "trends": (
                trends_df.to_dicts()
                if isinstance(trends_df, pl.DataFrame)
                else trends_df.to_dict("records")
            ),
            "time_unit": self.results[TrendResult.TIME_UNIT],
            "n_trends": self.results[TrendResult.N_TRENDS],
            "time_bounds": {
                "start": time_bounds.start.isoformat(),
                "end": time_bounds.end.isoformat(),
            },
            "config": config,
        }

    def _build_cli_report_impl(self) -> str:
        """Build CLI report content.

        Returns
        -------
        str
            Human-readable report content.

        Constitution References
        -----------------------
        - Section 8: CLI reporting format
        - Section 15: Flags warning in CLI output
        """
        lines = []
        lines.append("Trend Analysis Summary:")
        lines.append("=" * 70)
        lines.append("")

        # Configuration
        config = self.results[TrendResult.CONFIG]
        time_unit = config["time_unit"]
        lines.append(f"Time Unit: {time_unit}")

        group_by = config.get("group_by")
        if group_by:
            lines.append(f"Grouped by: {', '.join(group_by)}")
        else:
            lines.append("Grouping: Global (no grouping)")

        min_samples = config.get("min_samples", 3)
        min_duration_years = config.get("min_duration_years", 1.0)
        lines.append(f"Minimum samples: {min_samples}")
        lines.append(f"Minimum duration: {min_duration_years} years")
        lines.append("")

        # Time bounds
        time_bounds = self.results[TrendResult.TIME_BOUNDS]
        lines.append(
            f"Time Range: {time_bounds.start.isoformat()} to {time_bounds.end.isoformat()}"
        )
        lines.append("")

        # Results summary
        trends_df = self.results[TrendResult.TRENDS]
        n_trends = len(trends_df)
        lines.append(f"Number of trends computed: {n_trends}")
        lines.append("")

        # Show summary table
        if n_trends > 0:
            lines.append("Trend Results:")
            lines.append("-" * 70)

            # Display top trends
            category_col = self.config.get(TrendConfig.CATEGORY_COL, "pollutant")
            for row in trends_df.iter_rows(named=True):
                cat_val = row.get(category_col, "Unknown")
                slope = row.get("slope", 0.0)
                intercept = row.get("intercept", 0.0)
                r_squared = row.get("r_squared", 0.0)
                n = row.get("n", 0)
                duration_years = row.get("duration_years", 0.0)
                slope_units = row.get("slope_units", "unknown")

                lines.append(
                    f"  {cat_val}: slope={slope:.4f} {slope_units}, "
                    f"intercept={intercept:.4f}, R²={r_squared:.4f}, "
                    f"n={n}, duration={duration_years:.2f} years"
                )

                # Show flags if present
                short_duration_flag = row.get("short_duration_flag", False)
                low_n_flag = row.get("low_n_flag", False)
                if short_duration_flag or low_n_flag:
                    flags_str = []
                    if short_duration_flag:
                        flags_str.append("SHORT_DURATION")
                    if low_n_flag:
                        flags_str.append("LOW_N")
                    lines.append(f"    ⚠ Flags: {', '.join(flags_str)}")

            lines.append("")

        return "\n".join(lines)

    def _validate_config_impl(self) -> None:
        """Validate configuration."""
        # Check time_unit is valid
        time_unit = self.config.get(TrendConfig.TIME_UNIT)
        if time_unit is not None:
            if isinstance(time_unit, str):
                try:
                    TimeUnit(time_unit)
                except ValueError:
                    raise ValueError(
                        f"Invalid time_unit: {time_unit}. Must be one of {[u.value for u in TimeUnit]}"
                    )
            elif not isinstance(time_unit, TimeUnit):
                raise TypeError(
                    f"time_unit must be TimeUnit enum or string, got {type(time_unit)}"
                )
