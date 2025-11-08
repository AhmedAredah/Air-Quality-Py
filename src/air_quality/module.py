"""air_quality.module

Base module class for all air quality analysis modules.

Constitution compliance:
- Section 7: AirQualityModule is the single root base class
- Section 7: Required public entrypoints (from_dataframe, from_dataset, run, report_dashboard, report_cli)
- Section 7: Required hooks for subclasses
- Section 8: Dual reporting (dashboard + CLI)
- Section 15: Provenance attachment via run()
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Sequence, TypedDict

import pandas as pd

from .dataset.base import BaseDataset
from .exceptions import ConfigurationError, DataValidationError
from .logging import get_logger
from .mapping import ColumnMapper, ColumnMappingResult
from .provenance import ProvenanceRecord, make_provenance


class DashboardPayload(TypedDict):
    """Type definition for dashboard report payload.

    Constitution Section 8: Dashboard payload MUST include module, domain,
    schema_version, provenance, and metrics.

    Attributes
    ----------
    module : str
        MODULE_NAME from the module class.
    domain : str
        DOMAIN from the module class (e.g., 'qc', 'pmf', 'health').
    schema_version : str
        OUTPUT_SCHEMA_VERSION from the module class.
    provenance : dict
        Provenance record including config_hash, run_timestamp, software_version.
    metrics : dict
        Module-specific metrics (value + units where applicable).
    """

    module: str
    domain: str
    schema_version: str
    provenance: Dict[str, Any]
    metrics: Dict[str, Any]


class AirQualityModule(ABC):
    """Abstract base class for all air quality analysis modules.

    Template-method pattern with lifecycle hooks for validation, computation,
    and post-processing. All subclasses MUST implement required hooks.

    Constitution References
    -------
    - Section 7: Core Architecture & AirQualityModule Interface
    - Section 8: Reporting & Visualization (dual reporting modes)
    - Section 15: Provenance attachment

    Class Attributes
    ----------------
    MODULE_NAME : str
        Unique module identifier (e.g., "row_count", "pmf").
    DOMAIN : str
        Analysis domain (e.g., "qc", "source_apportionment").
    OUTPUT_SCHEMA_VERSION : str
        Schema version for dashboard output.

    Instance Attributes
    -------------------
    dataset : BaseDataset
        Canonical dataset with LazyFrame backend.
    config : dict
        Module configuration parameters.
    metadata : dict
        Additional metadata (site info, time ranges, etc.).
    results : dict
        Computed results populated by run().
    provenance : ProvenanceRecord | None
        Provenance record attached after run().
    logger : LoggerAdapter
        Structured logger with module context.

    Public Methods
    --------------
    from_dataframe(df, *, config, column_mapping, metadata, column_mapper)
        Construct module from pandas DataFrame with column mapping.
    from_dataset(dataset, *, config, metadata)
        Construct module from existing canonical dataset.
    run(operations)
        Execute module lifecycle (validate, compute, attach provenance).
    report_dashboard()
        Generate structured dashboard payload (JSON-serializable dict).
    report_cli()
        Generate human-readable CLI report (string).

    Protected Hooks (Subclasses MUST implement)
    --------------------------------------------
    _get_required_columns() -> dict[str, list[str]] | list[str]
        Return required canonical columns or synonym mappings.
    _dataset_from_mapped_df(mapping_result) -> BaseDataset
        Construct appropriate dataset type from mapping result.
    _run_impl(operations) -> None
        Core computation logic; populate self.results.
    _build_dashboard_report_impl() -> dict[str, Any]
        Build module-specific dashboard metrics.
    _build_cli_report_impl() -> str
        Build human-readable CLI report content.
    _validate_config_impl() -> None
        Validate module-specific configuration.
    _validate_dataset() -> None
        Validate dataset meets module requirements (extendable).
    """

    # Class invariants (subclasses MUST define)
    MODULE_NAME: str
    DOMAIN: str
    OUTPUT_SCHEMA_VERSION: str

    def __init__(
        self,
        dataset: BaseDataset,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize module with dataset.

        Parameters
        ----------
        dataset : BaseDataset
            Canonical dataset with validated schema.
        config : dict, optional
            Module configuration parameters.
        metadata : dict, optional
            Additional metadata.

        Raises
        ------
        ConfigurationError
            If config validation fails.
        """
        self.dataset = dataset
        self.config = config or {}
        self.metadata = metadata or {}
        self.results: Dict[str, Any] = {}
        self.provenance: Optional[ProvenanceRecord] = None
        self._has_run = False

        # Structured logger with module context
        self.logger = get_logger(
            name=f"air_quality.{self.MODULE_NAME}",
            module=self.MODULE_NAME,
            domain=self.DOMAIN,
        )

        # Validate configuration
        self._validate_config_impl()

    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        *,
        config: Optional[Dict[str, Any]] = None,
        column_mapping: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        column_mapper: Optional[ColumnMapper] = None,
        include_candidate_suggestions: bool = False,
    ) -> AirQualityModule:
        """Construct module from pandas DataFrame with column mapping.

        Performs three-level column mapping (explicit → fuzzy → validation)
        using required columns from subclass, then constructs dataset.

        Parameters
        ----------
        df : pd.DataFrame
            Input data with arbitrary column names.
        config : dict, optional
            Module configuration parameters.
        column_mapping : dict[str, str], optional
            Explicit mapping from canonical to original column names.
        metadata : dict, optional
            Additional metadata.
        column_mapper : ColumnMapper, optional
            Custom column mapper instance (uses default if None).
        include_candidate_suggestions : bool, default=False
            Include candidate suggestions in diagnostics for unresolved fields.

        Returns
        -------
        AirQualityModule
            Constructed module instance.

        Raises
        ------
        SchemaError
            If required columns are missing or ambiguous.
        ConfigurationError
            If configuration is invalid.
        """
        # Get required columns from subclass
        required_columns = cls._get_required_columns_static()

        # Perform column mapping (constitution Section 3: centralized mapping)
        mapper = column_mapper or ColumnMapper()

        # Handle both dict (with synonyms) and list (canonical names only)
        if isinstance(required_columns, dict):
            synonyms = required_columns
            required = list(synonyms.keys())
        else:
            synonyms = {}
            required = list(required_columns)

        mapping_result = mapper.map(
            df,
            required=required,
            synonyms=synonyms,
            explicit=column_mapping,
            include_candidate_suggestions=include_candidate_suggestions,
        )

        # Store mapping metadata
        if metadata is None:
            metadata = {}
        metadata["column_mapping"] = mapping_result.mapping
        metadata["column_mapping_diagnostics"] = mapping_result.diagnostics

        # Construct dataset from mapped DataFrame
        dataset = cls._dataset_from_mapped_df_static(mapping_result, metadata)

        # Construct module
        return cls(dataset=dataset, config=config, metadata=metadata)

    @classmethod
    def from_dataset(
        cls,
        dataset: BaseDataset,
        *,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AirQualityModule:
        """Construct module from existing canonical dataset.

        Parameters
        ----------
        dataset : BaseDataset
            Canonical dataset with validated schema.
        config : dict, optional
            Module configuration parameters.
        metadata : dict, optional
            Additional metadata.

        Returns
        -------
        AirQualityModule
            Constructed module instance.

        Raises
        ------
        ConfigurationError
            If configuration is invalid.
        """
        return cls(dataset=dataset, config=config, metadata=metadata)

    def run(
        self,
        operations: Optional[Sequence[Enum]] = None,
    ) -> AirQualityModule:
        """Execute module lifecycle with optional operation selection.

        Lifecycle:
        1. Validate dataset (_validate_dataset)
        2. Execute computation (_run_impl with operations)
        3. Post-process results (_post_process)
        4. Record timing and attach provenance

        Parameters
        ----------
        operations : Sequence[Enum], optional
            Specific operations to run (module-specific enums).
            If None, runs all default operations.

        Returns
        -------
        AirQualityModule
            Self for method chaining.

        Raises
        ------
        DataValidationError
            If dataset validation fails.
        ConfigurationError
            If configuration is invalid.
        RuntimeError
            If run() called multiple times (idempotence enforcement).

        Notes
        -----
        Constitution Section 7: Single execution idempotence enforced.
        Constitution Section 15: Provenance attached uniformly.
        """
        # Enforce single execution (constitution Section 7)
        if self._has_run:
            raise RuntimeError(
                f"{self.MODULE_NAME}: run() can only be called once. "
                "Create a new module instance for another run."
            )

        self.logger.info(
            "Starting module execution", extra={"operations": str(operations)}
        )
        start_time = time.time()

        # 1. Validate dataset
        self._validate_dataset()

        # 2. Execute computation
        self._run_impl(operations=operations)

        # 3. Post-process results
        self._post_process()

        # 4. Record timing and attach provenance
        elapsed_seconds = time.time() - start_time
        self.results["_elapsed_seconds"] = elapsed_seconds

        self.provenance = make_provenance(
            module_name=self.MODULE_NAME,
            domain=self.DOMAIN,
            dataset_id=self.dataset.get_dataset_id(),
            config=self.config,
            extra={"elapsed_seconds": elapsed_seconds},
        )

        self._has_run = True
        self.logger.info(
            "Module execution completed", extra={"elapsed_seconds": elapsed_seconds}
        )

        return self

    def report_dashboard(self) -> DashboardPayload:
        """Generate structured dashboard payload.

        Returns
        -------
        DashboardPayload
            Dashboard payload with keys:
            - module: MODULE_NAME
            - domain: DOMAIN
            - schema_version: OUTPUT_SCHEMA_VERSION
            - provenance: dict from ProvenanceRecord
            - metrics: module-specific metrics

        Raises
        ------
        RuntimeError
            If called before run().

        Notes
        -----
        Constitution Section 8: Dashboard includes provenance & metrics.
        """
        if not self._has_run:
            raise RuntimeError(
                f"{self.MODULE_NAME}: must call run() before report_dashboard()"
            )

        if self.provenance is None:
            raise RuntimeError(
                f"{self.MODULE_NAME}: provenance not attached (should never happen)"
            )

        return {
            "module": self.MODULE_NAME,
            "domain": self.DOMAIN,
            "schema_version": self.OUTPUT_SCHEMA_VERSION,
            "provenance": self.provenance.to_dict(),
            "metrics": self._build_dashboard_report_impl(),
        }

    def report_cli(self) -> str:
        """Generate human-readable CLI report.

        Returns
        -------
        str
            Multi-line CLI report including:
            - Module header
            - Input summary (dataset rows, columns)
            - Column mapping summary
            - Module-specific content
            - Provenance summary

        Raises
        ------
        RuntimeError
            If called before run().

        Notes
        -----
        Constitution Section 8: CLI includes inputs, methods, results, mapping.
        """
        if not self._has_run:
            raise RuntimeError(
                f"{self.MODULE_NAME}: must call run() before report_cli()"
            )

        lines = []
        lines.append("=" * 70)
        lines.append(f"Module: {self.MODULE_NAME} (Domain: {self.DOMAIN})")
        lines.append("=" * 70)
        lines.append("")

        # Input summary
        lines.append("Input Dataset:")
        lines.append(f"  Rows: {self.dataset.n_rows}")
        lines.append(f"  Columns: {list(self.dataset.schema.keys())}")
        lines.append("")

        # Column mapping summary (constitution Section 3: mapping in reports)
        if "column_mapping" in self.metadata:
            lines.append("Column Mapping:")
            for canonical, original in self.metadata["column_mapping"].items():
                lines.append(f"  {canonical} <- {original}")
            lines.append("")

        # Module-specific content
        lines.append(self._build_cli_report_impl())
        lines.append("")

        # Provenance summary
        if self.provenance:
            lines.append("Provenance:")
            lines.append(f"  Run Timestamp: {self.provenance.run_timestamp}")
            lines.append(f"  Software Version: {self.provenance.software_version}")
            lines.append(f"  Config Hash: {self.provenance.config_hash}")
            if self.provenance.dataset_id:
                lines.append(f"  Dataset ID: {self.provenance.dataset_id}")

        lines.append("=" * 70)

        return "\n".join(lines)

    def _validate_dataset(self) -> None:
        """Validate dataset meets module requirements.

        Base implementation checks non-empty. Subclasses can extend
        with additional validations (call super()._validate_dataset() first).

        Raises
        ------
        DataValidationError
            If dataset is empty or invalid.
        """
        if self.dataset.is_empty():
            raise DataValidationError(f"{self.MODULE_NAME}: dataset cannot be empty")

    def _post_process(self) -> None:
        """Post-process results after computation.

        Base implementation is a no-op. Subclasses can override
        to add QC flags, derived metrics, etc.
        """
        pass

    # Abstract methods (subclasses MUST implement)

    @classmethod
    @abstractmethod
    def _get_required_columns_static(cls) -> Dict[str, list[str]] | list[str]:
        """Return required canonical columns or synonym mappings.

        Returns
        -------
        dict[str, list[str]] or list[str]
            Either a dict mapping canonical names to synonym lists,
            or a simple list of canonical column names.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def _dataset_from_mapped_df_static(
        cls,
        mapping_result: ColumnMappingResult,
        metadata: Dict[str, Any],
    ) -> BaseDataset:
        """Construct appropriate dataset type from mapping result.

        Parameters
        ----------
        mapping_result : ColumnMappingResult
            Result of column mapping operation.
        metadata : dict
            Metadata including mapping diagnostics.

        Returns
        -------
        BaseDataset
            Constructed dataset instance.
        """
        raise NotImplementedError

    @abstractmethod
    def _run_impl(
        self,
        operations: Optional[Sequence[Enum]] = None,
    ) -> None:
        """Core computation logic.

        Subclasses implement analysis here. Populate self.results dict.

        Parameters
        ----------
        operations : Sequence[Enum], optional
            Specific operations to run (module-specific enums).
            If None, run all default operations.
        """
        raise NotImplementedError

    @abstractmethod
    def _build_dashboard_report_impl(self) -> Dict[str, Any]:
        """Build module-specific dashboard metrics.

        Returns
        -------
        dict
            Module-specific metrics for dashboard.
        """
        raise NotImplementedError

    @abstractmethod
    def _build_cli_report_impl(self) -> str:
        """Build human-readable CLI report content.

        Returns
        -------
        str
            Module-specific CLI report content.
        """
        raise NotImplementedError

    @abstractmethod
    def _validate_config_impl(self) -> None:
        """Validate module-specific configuration.

        Raises
        ------
        ConfigurationError
            If configuration is invalid.
        """
        raise NotImplementedError
