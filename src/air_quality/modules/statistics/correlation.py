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

import polars as pl

from ...analysis.correlation import OutputFormat, compute_pairwise, CorrelationOperation
from ...dataset.base import BaseDataset
from ...dataset.time_series import TimeSeriesDataset
from ...mapping import ColumnMappingResult
from ...module import AirQualityModule, ModuleDomain
from ...time_utils import compute_time_bounds


class CorrelationConfig(str, Enum):
    """Configuration keys for correlation analysis module.

    Constitution References
    -----------------------
    - Section 7: Module configuration standards
    - Section 15: Units enforcement policy

    Attributes
    ----------
    GROUP_BY : str
        Grouping columns (None for global aggregation).
    MIN_SAMPLES : str
        Minimum number of valid pairwise observations.
    ALLOW_MISSING_UNITS : str
        Whether to allow correlation with missing unit metadata.
    CATEGORY_COL : str
        Category identifier column name (e.g., 'pollutant').
    VALUE_COLS : str
        Value column(s) to analyze (single string or list of strings).
    FLAG_COL : str
        QC flag column name.
    OUTPUT_FORMAT : str
        Output format (TIDY or WIDE).
    ALLOW_MIXED_UNIT_FAMILIES : str
        Whether to allow correlating variables with incompatible unit families.
    """

    GROUP_BY = "group_by"
    MIN_SAMPLES = "min_samples"
    ALLOW_MISSING_UNITS = "allow_missing_units"
    CATEGORY_COL = "category_col"
    VALUE_COLS = "value_cols"
    FLAG_COL = "flag_col"
    OUTPUT_FORMAT = "output_format"
    ALLOW_MIXED_UNIT_FAMILIES = "allow_mixed_unit_families"


class CorrelationResult(Enum):
    """Result keys for CorrelationModule.

    Attributes
    ----------
    CORRELATIONS : str
        DataFrame with correlation results.
    TIME_BOUNDS : str
        Time range of the dataset (start, end).
    N_PAIRS : str
        Number of correlation pairs computed.
    METHOD_USED : str
        Correlation method used (pearson/spearman).
    UNITS_STATUS : str
        Whether units were present or overridden.
    """

    CORRELATIONS = "correlations"
    TIME_BOUNDS = "time_bounds"
    N_PAIRS = "n_pairs"
    METHOD_USED = "method_used"
    UNITS_STATUS = "units_status"


class CorrelationModuleName(Enum):
    """Module name identifier for correlation module."""

    VALUE = "correlation"


class CorrelationSchemaVersion(Enum):
    """Output schema version for correlation module."""

    V1_0_0 = "1.0.0"


class CorrelationModule(AirQualityModule):
    """Module for computing pairwise correlations across categories.

    This module provides pairwise correlation analysis including:
    - Pearson correlation (linear relationships)
    - Spearman correlation (monotonic relationships)
    - Ordered unique pairs (var_x <= var_y)
    - Optional grouping by site_id or other dimensions
    - QC-aware filtering
    - Unit enforcement (configurable override)
    - Unit family validation (prevents correlating incompatible physical quantities)

    Operations
    ----------
    - PEARSON: Compute Pearson correlation (linear relationships)
    - SPEARMAN: Compute Spearman correlation (monotonic relationships)

    Constitution compliance:
    - Section 7: Inherits AirQualityModule, implements required hooks
    - Section 8: Dual reporting (dashboard + CLI)
    - Section 11: Uses Polars vectorized operations
    - Section 15: Provenance attachment with units status

    Examples
    --------
    >>> import pandas as pd
    >>> from air_quality.modules.statistics.correlation import (
    ...     CorrelationModule,
    ...     CorrelationOperation,
    ...     CorrelationResult
    ... )
    >>> from air_quality.qc_flags import QCFlag
    >>> from air_quality.dataset.time_series import TimeSeriesDataset
    >>> df = pd.DataFrame({
    ...     'datetime': pd.date_range('2024-01-01', periods=100, freq='h'),
    ...     'site_id': ['site1'] * 100,
    ...     'pollutant': ['PM25'] * 50 + ['PM10'] * 50,
    ...     'conc': range(100),
    ...     'flag': [QCFlag.VALID.value] * 100
    ... })
    >>> dataset = TimeSeriesDataset.from_dataframe(df, column_units={'conc': 'ug/m3'})
    >>> module = CorrelationModule(
    ...     dataset=dataset,
    ...     config={
    ...         'group_by': None,
    ...         'category_col': 'pollutant',
    ...         'value_cols': 'conc'
    ...     }
    ... )
    >>> module.run(operations=[CorrelationOperation.PEARSON])
    >>> module.run()
    >>> correlations = module.get_result(CorrelationResult.CORRELATIONS)
    """

    MODULE_NAME = CorrelationModuleName.VALUE
    DOMAIN = ModuleDomain.STATISTICS
    OUTPUT_SCHEMA_VERSION = CorrelationSchemaVersion.V1_0_0

    ConfigKey = CorrelationConfig

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
            "CorrelationModule._dataset_from_mapped_df_static not yet implemented"
        )

    def _run_impl(self, operations: Optional[Sequence[Enum]] = None) -> None:
        """Execute correlation analysis.

        Parameters
        ----------
        operations : Sequence[CorrelationOperation], optional
            Correlation methods to compute. If None, computes all methods.
            Options: PEARSON, SPEARMAN
        """
        # Determine which correlation methods to compute
        if operations is None:
            # Compute Pearson correlation by default
            ops_to_run = [CorrelationOperation.PEARSON]
        else:
            # Cast to list of CorrelationOperation for type safety
            ops_to_run = [CorrelationOperation(op) for op in operations]

        self.logger.info(f"Computing correlations: {[op.value for op in ops_to_run]}")

        # Compute correlations for each requested method
        for op in ops_to_run:
            correlation_type = op  # CorrelationOperation enum member
            self._compute_correlations(correlation_type=correlation_type)

    def _validate_unit_families(
        self,
        value_cols: list[str],
        allow_mixed: bool,
    ) -> None:
        """Validate that all value columns have compatible unit families.

        Checks if units across multiple value columns belong to the same family
        (e.g., ug/m3 and mg/m3 are both MASS_CONCENTRATION).
        Raises error if incompatible families detected across columns unless override enabled.

        Parameters
        ----------
        value_cols : list[str]
            List of value column names to validate.
        allow_mixed : bool
            If True, allows mixed families across columns with warning. If False, raises error.

        Raises
        ------
        UnitError
            If incompatible unit families detected across columns and allow_mixed=False.
        """
        from ...exceptions import UnitError
        from ...units import Unit, UnitFamily

        # Cast to TimeSeriesDataset for type checker
        assert isinstance(self.dataset, TimeSeriesDataset)

        # Skip validation if no units
        if self.dataset.column_units is None:
            return

        # Collect unit families from each value column
        column_families: dict[str, tuple[str, UnitFamily]] = {}

        for value_col in value_cols:
            # Skip if column has no unit
            if value_col not in self.dataset.column_units:
                continue

            value_unit = self.dataset.column_units[value_col]

            # If it's a Unit enum, extract family
            if isinstance(value_unit, Unit):
                # Unit enum has structure: (symbol, family, factor, precision)
                symbol = value_unit.value[0]
                family = value_unit.value[1]  # Get UnitFamily from tuple
                column_families[value_col] = (symbol, family)

                self.logger.info(
                    f"Unit family validation: {value_col} uses {symbol} "
                    f"(family: {family.value})"
                )
            else:
                # If column_units contains string (shouldn't happen with proper validation),
                # we can't determine family - log warning
                self.logger.warning(
                    f"Cannot validate unit family for {value_col}: "
                    f"unit is {type(value_unit)}, expected Unit enum"
                )

        # Check if all columns have the same unit family
        if len(column_families) > 1:
            families = {family for _, family in column_families.values()}

            if len(families) > 1:
                # Mixed families detected
                family_details = ", ".join(
                    f"{col} ({family.value})"
                    for col, (_, family) in column_families.items()
                )

                if not allow_mixed:
                    raise UnitError(
                        f"Cannot correlate columns with different unit families: {family_details}. "
                        f"Set ALLOW_MIXED_UNIT_FAMILIES=True to override if correlation is scientifically valid."
                    )
                else:
                    self.logger.warning(
                        f"Correlating columns with different unit families: {family_details}. "
                        f"Ensure this correlation is scientifically meaningful."
                    )

    def _compute_correlations(self, correlation_type: CorrelationOperation) -> None:
        """Compute pairwise correlations with QC-aware filtering and unit enforcement.

        Parameters
        ----------
        correlation_type : CorrelationOperation
            Correlation method to use (CorrelationOperation.PEARSON or CorrelationOperation.SPEARMAN).
        """
        self.logger.info(f"Computing {correlation_type} pairwise correlations")

        # Extract configuration
        group_by = self.config.get(CorrelationConfig.GROUP_BY, None)
        min_samples = self.config.get(CorrelationConfig.MIN_SAMPLES, 3)
        allow_missing_units = self.config.get(
            CorrelationConfig.ALLOW_MISSING_UNITS, False
        )
        category_col = self.config.get(CorrelationConfig.CATEGORY_COL, "pollutant")
        value_cols = self.config.get(CorrelationConfig.VALUE_COLS, "conc")
        flag_col = self.config.get(CorrelationConfig.FLAG_COL, "flag")
        output_format = self.config.get(
            CorrelationConfig.OUTPUT_FORMAT, OutputFormat.TIDY
        )
        allow_mixed_unit_families = self.config.get(
            CorrelationConfig.ALLOW_MIXED_UNIT_FAMILIES, False
        )

        # Validate unit families across all value columns
        value_cols_list = [value_cols] if isinstance(value_cols, str) else value_cols
        self._validate_unit_families(value_cols_list, allow_mixed_unit_families)

        # Compute correlations
        corr_df = compute_pairwise(
            dataset=self.dataset,
            group_by=group_by,
            correlation_type=correlation_type,
            category_col=category_col,
            value_cols=value_cols,
            flag_col=flag_col,
            min_samples=min_samples,
            allow_missing_units=allow_missing_units,
            output_format=output_format,
        )

        # Store results
        self.results[CorrelationResult.CORRELATIONS] = corr_df
        self.results[CorrelationResult.METHOD_USED] = correlation_type.value
        self.results[CorrelationResult.N_PAIRS] = len(corr_df)

        # Determine units status (check all value columns)
        # Must check on TimeSeriesDataset for column_units attribute
        assert isinstance(self.dataset, TimeSeriesDataset)

        # Normalize value_cols to list for checking
        value_cols_list = [value_cols] if isinstance(value_cols, str) else value_cols

        has_units = self.dataset.column_units is not None and all(
            col in self.dataset.column_units for col in value_cols_list
        )
        units_status = (
            "present"
            if has_units
            else "overridden" if allow_missing_units else "missing"
        )
        self.results[CorrelationResult.UNITS_STATUS] = units_status

        # Compute time bounds for provenance
        time_bounds = compute_time_bounds(
            self.dataset.lazyframe,
            time_col=self.dataset.time_index_name,
        )
        self.results[CorrelationResult.TIME_BOUNDS] = time_bounds

        self.logger.info(
            f"Computed {len(corr_df)} correlation pairs using {correlation_type}"
        )

    def _build_dashboard_report_impl(self) -> Dict[str, Any]:
        """Build dashboard metrics.

        Returns
        -------
        dict
            Metrics including correlation results, method, and units status.

        Constitution References
        -----------------------
        - Section 8: Dashboard reporting format
        - Section 15: Units provenance in dashboard output
        """
        corr_df = self.results[CorrelationResult.CORRELATIONS]
        time_bounds = self.results[CorrelationResult.TIME_BOUNDS]

        # Convert to dict for JSON serialization
        return {
            "correlations": (
                corr_df.to_dicts()
                if isinstance(corr_df, pl.DataFrame)
                else corr_df.to_dict("records")
            ),
            "method": self.results[CorrelationResult.METHOD_USED],
            "n_pairs": self.results[CorrelationResult.N_PAIRS],
            "units_status": self.results[CorrelationResult.UNITS_STATUS],
            "time_bounds": {
                "start": time_bounds.start.isoformat(),
                "end": time_bounds.end.isoformat(),
            },
            "config": {
                "group_by": self.config.get(CorrelationConfig.GROUP_BY),
                "min_samples": self.config.get(CorrelationConfig.MIN_SAMPLES, 3),
                "allow_missing_units": self.config.get(
                    CorrelationConfig.ALLOW_MISSING_UNITS, False
                ),
            },
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
        - Section 15: Units warning in CLI output
        """
        lines = []
        lines.append("Correlation Analysis Summary:")
        lines.append("=" * 70)
        lines.append("")

        # Method and configuration
        method = self.results[CorrelationResult.METHOD_USED]
        lines.append(f"Method: {method.upper()}")

        group_by = self.config.get(CorrelationConfig.GROUP_BY)
        if group_by:
            lines.append(f"Grouped by: {', '.join(group_by)}")
        else:
            lines.append("Grouping: Global (no grouping)")

        min_samples = self.config.get(CorrelationConfig.MIN_SAMPLES, 3)
        lines.append(f"Minimum samples: {min_samples}")
        lines.append("")

        # Time bounds
        time_bounds = self.results[CorrelationResult.TIME_BOUNDS]
        lines.append(
            f"Time Range: {time_bounds.start.isoformat()} to {time_bounds.end.isoformat()}"
        )
        lines.append("")

        # Units warning
        units_status = self.results[CorrelationResult.UNITS_STATUS]
        if units_status == "overridden":
            lines.append(
                "⚠ WARNING: Unit metadata missing - correlations computed without unit checks"
            )
            lines.append("   Set allow_missing_units=False to enforce unit presence")
            lines.append("")
        elif units_status == "present":
            lines.append("✓ Unit metadata present and validated")
            lines.append("")

        # Correlation results
        corr_df = self.results[CorrelationResult.CORRELATIONS]
        n_pairs = len(corr_df)
        lines.append(f"Total correlation pairs: {n_pairs}")
        lines.append("")

        if n_pairs == 0:
            lines.append("No correlation pairs computed (insufficient data)")
            return "\n".join(lines)

        # Convert to pandas for display if needed
        if isinstance(corr_df, pl.DataFrame):
            display_df = corr_df.to_pandas()
        else:
            display_df = corr_df

        # Show correlation matrix if global (no grouping)
        if not group_by:
            lines.append("Correlation Matrix:")
            lines.append("-" * 70)

            # Create pivot table for matrix display
            try:
                import pandas as pd

                pivot_df = display_df.pivot(
                    index="var_x", columns="var_y", values="correlation"
                )
                # Fill diagonal and symmetric elements
                for var in pivot_df.index:
                    if var in pivot_df.columns:
                        pivot_df.loc[var, var] = 1.0

                # Format with 3 decimal places
                lines.append(pivot_df.to_string(float_format=lambda x: f"{x:6.3f}"))
            except Exception:
                # Fallback to table format
                lines.append(display_df.to_string(index=False))

            lines.append("")

            # Show top positive and negative correlations (excluding diagonal)
            non_diag = display_df[display_df["var_x"] != display_df["var_y"]]
            if len(non_diag) > 0:
                lines.append("Top Correlations:")
                lines.append("  Strongest positive:")
                top_pos = non_diag.nlargest(3, "correlation")
                for _, row in top_pos.iterrows():
                    lines.append(
                        f"    {row['var_x']} - {row['var_y']}: {row['correlation']:6.3f} (n={row['n']})"
                    )

                lines.append("  Strongest negative:")
                top_neg = non_diag.nsmallest(3, "correlation")
                for _, row in top_neg.iterrows():
                    lines.append(
                        f"    {row['var_x']} - {row['var_y']}: {row['correlation']:6.3f} (n={row['n']})"
                    )
        else:
            # Show grouped results
            lines.append("Correlation Results by Group:")
            lines.append("-" * 70)

            # Group and display
            for group_vals in (
                display_df[group_by].drop_duplicates().itertuples(index=False)
            ):
                if len(group_by) == 1:
                    group_str = f"{group_by[0]}={group_vals[0]}"
                    group_filter = display_df[group_by[0]] == group_vals[0]
                else:
                    group_str = ", ".join(
                        f"{col}={val}" for col, val in zip(group_by, group_vals)
                    )
                    group_filter = True
                    for col, val in zip(group_by, group_vals):
                        group_filter &= display_df[col] == val

                group_data = display_df[group_filter]
                lines.append(f"\n{group_str}:")

                # Show non-diagonal correlations
                non_diag_group = group_data[group_data["var_x"] != group_data["var_y"]]
                if len(non_diag_group) > 0:
                    for _, row in non_diag_group.iterrows():
                        lines.append(
                            f"  {row['var_x']} - {row['var_y']}: {row['correlation']:6.3f} (n={row['n']})"
                        )
                else:
                    lines.append("  No cross-correlations (single variable)")

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)

    def _validate_config_impl(self) -> None:
        """Validate configuration."""
        # Validate min_samples
        min_samples = self.config.get(CorrelationConfig.MIN_SAMPLES, 3)
        if not isinstance(min_samples, int) or min_samples < 2:
            raise ValueError(f"min_samples must be an integer >= 2, got: {min_samples}")
