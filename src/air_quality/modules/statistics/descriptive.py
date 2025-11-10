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

import polars as pl

from ...analysis.descriptive import compute_descriptives
from ...dataset.base import BaseDataset
from ...dataset.time_series import TimeSeriesDataset
from ...exceptions import ConfigurationError
from ...mapping import ColumnMappingResult
from ...module import AirQualityModule, ModuleDomain
from ...time_utils import compute_time_bounds


class DescriptiveStatsModuleName(Enum):
    """Module name identifier for descriptive statistics module."""

    VALUE = "descriptive_statistics"


class DescriptiveStatsSchemaVersion(Enum):
    """Output schema version for descriptive statistics module."""

    V1_0_0 = "1.0.0"


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


class DescriptiveStatsMetadata(Enum):
    """Metadata keys for DescriptiveStatsModule.

    Attributes
    ----------
    SITE_NAME : str
        Optional human-readable site name.
    ANALYSIS_PURPOSE : str
        Optional description of analysis purpose.
    """

    SITE_NAME = "site_name"
    ANALYSIS_PURPOSE = "analysis_purpose"


class DescriptiveStatsResult(Enum):
    """Result keys for DescriptiveStatsModule.

    Attributes
    ----------
    STATISTICS : str
        Tidy dataframe with computed statistics.
    TIME_BOUNDS : str
        Time range of the dataset (start, end).
    N_TOTAL : str
        Total observations before filtering.
    N_VALID : str
        Valid observations used in computation.
    N_MISSING : str
        Missing observations (excluded + below_dl).
    """

    STATISTICS = "statistics"
    TIME_BOUNDS = "time_bounds"
    N_TOTAL = "n_total"
    N_VALID = "n_valid"
    N_MISSING = "n_missing"


class DescriptiveStatsModule(AirQualityModule):
    """Module for computing descriptive statistics per pollutant and grouping keys.

    This module provides comprehensive descriptive statistics including:
    - Mean, median, std, min, max
    - Quantiles (5th, 25th, 75th, 95th percentiles by default)
    - QC-aware counts (n_total, n_valid, n_missing)
    - Optional grouping by site_id or other dimensions

    Constitution compliance:
    - Section 7: Inherits AirQualityModule, implements required hooks
    - Section 8: Dual reporting (dashboard + CLI)
    - Section 11: Uses Polars vectorized operations
    - Section 15: Provenance attachment with time bounds and config

    Examples
    --------
    >>> import pandas as pd
    >>> from air_quality.modules.statistics.descriptive import DescriptiveStatsModule
    >>> from air_quality.qc_flags import QCFlag
    >>> df = pd.DataFrame({
    ...     'datetime': pd.date_range('2024-01-01', periods=100, freq='h'),
    ...     'site_id': ['A'] * 100,
    ...     'pollutant': ['PM2.5'] * 100,
    ...     'conc': range(100),
    ...     'flag': [QCFlag.VALID.value] * 100
    ... })
    >>> module = DescriptiveStatsModule.from_dataframe(df)
    >>> module.run()
    >>> stats = module.results[DescriptiveStatsResult.STATISTICS]
    >>> print(module.report_cli())
    """

    # Class invariants (required by AirQualityModule)
    MODULE_NAME = DescriptiveStatsModuleName.VALUE
    DOMAIN = ModuleDomain.STATISTICS
    OUTPUT_SCHEMA_VERSION = DescriptiveStatsSchemaVersion.V1_0_0

    # Enum types for type-safe config, metadata, and results
    ConfigKey = DescriptiveStatsConfig
    MetadataKey = DescriptiveStatsMetadata
    ResultKey = DescriptiveStatsResult

    @classmethod
    def _get_required_columns_static(cls) -> Dict[str, list[str]]:
        """Return required columns for time series dataset.

        Returns
        -------
        dict[str, list[str]]
            Mapping of canonical columns to synonym lists.
            For time series: datetime, site_id, pollutant, conc, flag (optional).
        """
        return {
            "datetime": ["timestamp", "time", "date"],
            "site_id": ["site", "location", "station_id"],
            "pollutant": ["species_id", "species", "parameter"],
            "conc": ["concentration", "value", "measurement"],
            "flag": ["qc_flag", "quality_flag", "status"],
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
        import pandas as pd

        # Add mapping metadata to dataset
        dataset_metadata = metadata.copy()
        if mapping_result.mapping:
            dataset_metadata["mapping"] = mapping_result.mapping

        # TimeSeriesDataset requires pandas DataFrame
        # If mapping result is Polars, convert to pandas
        df_for_dataset = mapping_result.df_mapped
        if hasattr(df_for_dataset, "to_pandas"):  # Polars DataFrame
            df_for_dataset = df_for_dataset.to_pandas()  # type: ignore[operator]

        # Ensure df_for_dataset is pandas DataFrame for type checker
        assert isinstance(df_for_dataset, pd.DataFrame)

        return TimeSeriesDataset.from_dataframe(
            df_for_dataset,
            metadata=dataset_metadata,
            mapping=mapping_result.mapping,
            time_index_name="datetime",
        )

    def _run_impl(
        self,
        operations: Optional[Sequence[Enum]] = None,
    ) -> None:
        """Execute descriptive statistics computation.

        Parameters
        ----------
        operations : Sequence[Enum], optional
            Not used for this module (single operation).
        """
        self.logger.info("Computing descriptive statistics")

        # Extract configuration
        group_by = self.config.get(DescriptiveStatsConfig.GROUP_BY, None)
        quantiles = self.config.get(DescriptiveStatsConfig.QUANTILES, None)
        pollutant_col = self.config.get(
            DescriptiveStatsConfig.POLLUTANT_COL, "pollutant"
        )
        conc_col = self.config.get(DescriptiveStatsConfig.CONC_COL, "conc")
        flag_col = self.config.get(DescriptiveStatsConfig.FLAG_COL, "flag")

        # Compute descriptive statistics
        stats_df = compute_descriptives(
            dataset=self.dataset,
            group_by=group_by,
            pollutant_col=pollutant_col,
            conc_col=conc_col,
            flag_col=flag_col,
            quantiles=quantiles,
        )

        # Store results
        self.results[DescriptiveStatsResult.STATISTICS] = stats_df

        # Compute time bounds for provenance
        # Cast to TimeSeriesDataset for type checker
        assert isinstance(self.dataset, TimeSeriesDataset)
        time_bounds = compute_time_bounds(
            self.dataset.lazyframe,
            time_col=self.dataset.time_index_name,
        )
        self.results[DescriptiveStatsResult.TIME_BOUNDS] = time_bounds

        # Extract aggregate counts (sum across all groups)
        total_counts = stats_df.select(
            pl.col("n_total").sum().alias("n_total"),
            pl.col("n_valid").sum().alias("n_valid"),
            pl.col("n_missing").sum().alias("n_missing"),
        ).to_dicts()[0]

        self.results[DescriptiveStatsResult.N_TOTAL] = total_counts["n_total"]
        self.results[DescriptiveStatsResult.N_VALID] = total_counts["n_valid"]
        self.results[DescriptiveStatsResult.N_MISSING] = total_counts["n_missing"]

        self.logger.info(
            f"Computed statistics: {stats_df.shape[0]} rows, "
            f"{total_counts['n_valid']}/{total_counts['n_total']} valid observations"
        )

    def _post_process(self) -> None:
        """Post-process results.

        Ensures all required results are populated.
        Provenance is handled automatically by base class run().
        """
        # Ensure results are populated
        if DescriptiveStatsResult.STATISTICS not in self.results:
            raise ConfigurationError(
                "Results not populated; run() must be called first"
            )

    def _build_dashboard_report_impl(self) -> Dict[str, Any]:
        """Build dashboard metrics.

        Returns
        -------
        dict
            Metrics including statistics dataframe and count summaries.
        """
        stats_df = self.results[DescriptiveStatsResult.STATISTICS]

        # Convert to dict for JSON serialization
        # Use Polars to_dicts() for efficient conversion
        return {
            "statistics": stats_df.to_dicts(),
            "n_total": self.results[DescriptiveStatsResult.N_TOTAL],
            "n_valid": self.results[DescriptiveStatsResult.N_VALID],
            "n_missing": self.results[DescriptiveStatsResult.N_MISSING],
            "time_bounds": {
                "start": self.results[
                    DescriptiveStatsResult.TIME_BOUNDS
                ].start.isoformat(),
                "end": self.results[DescriptiveStatsResult.TIME_BOUNDS].end.isoformat(),
            },
        }

    def _build_cli_report_impl(self) -> str:
        """Build CLI report content.

        Returns
        -------
        str
            Human-readable report content.
        """
        lines = []
        lines.append("Descriptive Statistics Summary:")
        lines.append("=" * 50)
        lines.append("")

        # Time bounds
        time_bounds = self.results[DescriptiveStatsResult.TIME_BOUNDS]
        lines.append(
            f"Time Range: {time_bounds.start.isoformat()} to {time_bounds.end.isoformat()}"
        )
        lines.append("")

        # QC summary
        lines.append("Quality Control Summary:")
        n_total = self.results[DescriptiveStatsResult.N_TOTAL]
        n_valid = self.results[DescriptiveStatsResult.N_VALID]
        n_missing = self.results[DescriptiveStatsResult.N_MISSING]

        lines.append(f"  Total Observations:   {n_total:>10,}")
        lines.append(f"  Valid Observations:   {n_valid:>10,}")
        lines.append(f"  Missing/Excluded:     {n_missing:>10,}")
        if n_total > 0:
            valid_pct = (n_valid / n_total) * 100
            lines.append(f"  Valid Percentage:     {valid_pct:>10.1f}%")
        lines.append("")

        # Statistics summary
        stats_df = self.results[DescriptiveStatsResult.STATISTICS]
        group_by = self.config.get(DescriptiveStatsConfig.GROUP_BY, None)

        if group_by:
            lines.append(f"Grouped by: {', '.join(group_by)}")
            lines.append("")

        # Get unique pollutants
        pollutants = stats_df.select("pollutant").unique().to_series().to_list()
        lines.append(f"Pollutants: {', '.join(pollutants)}")
        lines.append("")

        # Show summary table for each pollutant (mean, median, std)
        lines.append("Key Statistics:")
        lines.append("")

        for pollutant in pollutants:
            pollutant_stats = stats_df.filter(pl.col("pollutant") == pollutant)

            # Get mean, median, std (handle None/NaN values)
            def get_stat_value(stat_name: str) -> float | None:
                """Extract statistic value, handling None/NaN."""
                filtered = pollutant_stats.filter(pl.col("stat") == stat_name)
                if filtered.height == 0:
                    return None
                series = filtered.select("value").to_series()
                val = series[0]
                # Check for None or NaN
                if val is None or (isinstance(val, float) and val != val):  # NaN check
                    return None
                return float(val)  # Ensure return type is float
                return val

            mean_val = get_stat_value("mean")
            median_val = get_stat_value("median")
            std_val = get_stat_value("std")
            min_val = get_stat_value("min")
            max_val = get_stat_value("max")

            lines.append(f"  {pollutant}:")

            # Format with N/A for None values
            def format_val(val: float | None) -> str:
                return f"{val:>10.2f}" if val is not None else "       N/A"

            lines.append(f"    Mean:   {format_val(mean_val)}")
            lines.append(f"    Median: {format_val(median_val)}")
            lines.append(f"    Std:    {format_val(std_val)}")
            lines.append(f"    Min:    {format_val(min_val)}")
            lines.append(f"    Max:    {format_val(max_val)}")
            lines.append("")

        return "\n".join(lines)

    def _validate_config_impl(self) -> None:
        """Validate configuration.

        Raises
        ------
        ConfigurationError
            If configuration contains invalid values.
        """
        # Validate group_by if present
        if DescriptiveStatsConfig.GROUP_BY in self.config:
            group_by = self.config[DescriptiveStatsConfig.GROUP_BY]
            if group_by is not None and not isinstance(group_by, list):
                raise ConfigurationError(
                    f"group_by must be a list of column names, got {type(group_by)}"
                )

        # Validate quantiles if present
        if DescriptiveStatsConfig.QUANTILES in self.config:
            quantiles = self.config[DescriptiveStatsConfig.QUANTILES]
            if quantiles is not None:
                if not isinstance(quantiles, (list, tuple)):
                    raise ConfigurationError(
                        f"quantiles must be a list or tuple of floats, got {type(quantiles)}"
                    )
                # Check all values are between 0 and 1
                for q in quantiles:
                    if not (0 <= q <= 1):
                        raise ConfigurationError(
                            f"quantiles must be between 0 and 1, got {q}"
                        )
