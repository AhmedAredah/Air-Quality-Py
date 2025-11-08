"""air_quality.modules.row_count

Dummy row count module for foundational testing.

This module demonstrates the AirQualityModule interface with a minimal
computation: counting dataset rows and adding a simple QC flag.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional, Sequence

from ..dataset.base import BaseDataset
from ..dataset.time_series import TimeSeriesDataset
from ..exceptions import ConfigurationError
from ..mapping import ColumnMappingResult
from ..module import AirQualityModule


class RowCountOperation(Enum):
    """Operations available in RowCountModule.

    Attributes
    ----------
    COUNT_ROWS : str
        Count total number of rows in dataset.
    QC_CHECK : str
        Perform QC check (zero row validation).
    """

    COUNT_ROWS = "count_rows"
    QC_CHECK = "qc_check"


class RowCountModule(AirQualityModule):
    """Dummy module that counts rows in a dataset.

    This is a minimal example module for testing the AirQualityModule
    base class and lifecycle. It demonstrates:
    - Required columns specification
    - Dataset construction from mapping
    - Simple computation logic
    - QC flag generation
    - Dual reporting (dashboard + CLI)

    Operations
    ----------
    COUNT_ROWS : Count total rows
    QC_CHECK : Check for zero rows (should never occur)

    Results
    -------
    row_count : int
        Total number of rows in dataset.
    qc_zero_rows : bool
        True if zero rows detected (should never be True).

    Examples
    --------
    >>> import pandas as pd
    >>> from air_quality.modules import RowCountModule
    >>> df = pd.DataFrame({
    ...     'datetime': pd.date_range('2024-01-01', periods=10, freq='h'),
    ...     'site_id': ['A'] * 10,
    ...     'pollutant': ['PM2.5'] * 10,
    ...     'conc': range(10)
    ... })
    >>> module = RowCountModule.from_dataframe(df)
    >>> module.run()
    >>> module.results['row_count']
    10
    """

    # Class invariants (required by AirQualityModule)
    MODULE_NAME = "row_count"
    DOMAIN = "qc"
    OUTPUT_SCHEMA_VERSION = "1.0.0"

    @classmethod
    def _get_required_columns_static(cls) -> Dict[str, list[str]]:
        """Return required columns for time series dataset.

        Returns
        -------
        dict[str, list[str]]
            Mapping of canonical columns to synonym lists.
            For time series: datetime, site_id, pollutant/species_id, conc.
        """
        return {
            "datetime": ["timestamp", "time", "date"],
            "site_id": ["site", "location", "station_id"],
            "pollutant": ["species_id", "species", "parameter"],
            "conc": ["concentration", "value", "measurement"],
        }

    @classmethod
    def _dataset_from_mapped_df_static(
        cls,
        mapping_result: ColumnMappingResult,
        metadata: Dict[str, Any],
    ) -> BaseDataset:
        """Construct TimeSeriesDataset from mapping result.

        Parameters
        ----------
        mapping_result : ColumnMappingResult
            Result of column mapping with canonical columns.
        metadata : dict
            Metadata including mapping diagnostics.

        Returns
        -------
        TimeSeriesDataset
            Constructed time series dataset.
        """
        # Add mapping metadata to dataset
        dataset_metadata = metadata.copy()
        if mapping_result.mapping:
            dataset_metadata["mapping"] = mapping_result.mapping

        return TimeSeriesDataset.from_dataframe(
            mapping_result.df_mapped,
            metadata=dataset_metadata,
            mapping=mapping_result.mapping,
            time_index_name="datetime",
        )

    def _run_impl(
        self,
        operations: Optional[Sequence[Enum]] = None,
    ) -> None:
        """Execute row counting and QC checks.

        Parameters
        ----------
        operations : Sequence[RowCountOperation], optional
            Specific operations to run. If None, runs all operations.
        """
        # Determine which operations to run
        if operations is None:
            # Run all operations by default
            ops_to_run = list(RowCountOperation)
        else:
            # Cast to list of RowCountOperation for type safety
            ops_to_run = [RowCountOperation(op) for op in operations]

        self.logger.info(f"Running operations: {[op.value for op in ops_to_run]}")

        # Execute requested operations
        for op in ops_to_run:
            if op == RowCountOperation.COUNT_ROWS:
                self._count_rows()
            elif op == RowCountOperation.QC_CHECK:
                self._qc_check()
            else:
                self.logger.warning(f"Unknown operation: {op}")

    def _count_rows(self) -> None:
        """Count total rows in dataset."""
        # Use dataset property (triggers LazyFrame collection)
        row_count = self.dataset.n_rows
        self.results["row_count"] = row_count
        self.logger.info(f"Counted {row_count} rows")

    def _qc_check(self) -> None:
        """Perform QC check for zero rows.

        This should never detect zero rows since BaseDataset validates
        non-empty during construction. Included for demonstration.
        """
        row_count = self.results.get("row_count", self.dataset.n_rows)
        qc_zero_rows = row_count == 0

        self.results["qc_zero_rows"] = qc_zero_rows

        if qc_zero_rows:
            self.logger.warning("QC flag: Zero rows detected (should never happen)")
        else:
            self.logger.info("QC check passed: Non-zero rows")

    def _post_process(self) -> None:
        """Post-process results.

        Add additional QC flag if needed.
        """
        # Ensure both operations ran
        if "row_count" not in self.results:
            self._count_rows()

        if "qc_zero_rows" not in self.results:
            self._qc_check()

    def _build_dashboard_report_impl(self) -> Dict[str, Any]:
        """Build dashboard metrics.

        Returns
        -------
        dict
            Metrics including row_count and qc flags.
        """
        return {
            "row_count": self.results["row_count"],
            "qc_zero_rows": self.results["qc_zero_rows"],
        }

    def _build_cli_report_impl(self) -> str:
        """Build CLI report content.

        Returns
        -------
        str
            Human-readable report content.
        """
        lines = []
        lines.append("Row Count Analysis:")
        lines.append(f"  Total Rows: {self.results['row_count']}")
        lines.append("")
        lines.append("Quality Control:")

        if self.results["qc_zero_rows"]:
            lines.append("  ⚠ WARNING: Zero rows detected")
        else:
            lines.append("  ✓ PASS: Dataset contains rows")

        return "\n".join(lines)

    def _validate_config_impl(self) -> None:
        """Validate configuration.

        RowCountModule has no configuration parameters, so this is a no-op.

        Raises
        ------
        ConfigurationError
            If configuration contains unexpected keys.
        """
        # For this simple module, no configuration is needed
        # Could validate that config is empty if strict
        if self.config:
            # Allow but log unexpected config
            self.logger.warning(
                f"RowCountModule ignores configuration: {list(self.config.keys())}"
            )
