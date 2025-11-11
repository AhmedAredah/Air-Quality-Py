"""Unit tests for correlation unit family validation.

Tests unit family compatibility checking to prevent correlating
incompatible physical quantities.

Constitution References
-----------------------
- Section 15: Units enforcement for interpretability
- Section 15: Provenance tracking for unit override decisions

Test ID: T062
Module: air_quality.analysis.correlation + air_quality.modules.statistics.correlation
Focus: Unit family validation (MASS_CONCENTRATION vs VOLUME_CONCENTRATION)
"""

from __future__ import annotations

import pandas as pd
import polars as pl
import pytest

from air_quality.analysis.correlation import compute_pairwise
from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.modules.statistics.correlation import (
    CorrelationConfig,
    CorrelationModule,
    CorrelationOperation,
    CorrelationResult,
)
from air_quality.qc_flags import QCFlag
from air_quality.units import Unit


class TestCorrelationUnitFamilies:
    """Test unit family validation in correlation analysis."""

    def test_compatible_unit_families_pass(self) -> None:
        """Test correlation succeeds with compatible unit families (same family)."""
        # Create dataset with mass concentration units (ug/m3)
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        # Use Unit enum with MASS_CONCENTRATION family
        dataset = TimeSeriesDataset.from_dataframe(
            df, column_units={"conc": Unit.UG_M3}
        )

        # Should succeed (all pollutants in conc column share same unit)
        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=False,
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have 3 pairs
        assert len(result) == 3

    def test_unit_family_validation_via_module(self) -> None:
        """Test unit family validation via CorrelationModule."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(
            df, column_units={"conc": Unit.UG_M3}
        )

        # Should succeed with compatible units
        module = CorrelationModule(
            dataset=dataset,
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
                CorrelationConfig.ALLOW_MIXED_UNIT_FAMILIES: False,
            },
            
        )

        module.run(operations=[CorrelationOperation.PEARSON])

        correlations = module.results[CorrelationResult.CORRELATIONS]
        assert len(correlations) == 3

    def test_unit_family_override_allows_correlation(self) -> None:
        """Test allow_mixed_unit_families=True allows correlation."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(
            df, column_units={"conc": Unit.UG_M3}
        )

        module = CorrelationModule(
            dataset=dataset,
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
                CorrelationConfig.ALLOW_MIXED_UNIT_FAMILIES: True,  # Override
            },
            
        )

        module.run(operations=[CorrelationOperation.PEARSON])

        # Should succeed with override
        correlations = module.results[CorrelationResult.CORRELATIONS]
        if isinstance(correlations, pl.DataFrame):
            correlations = correlations.to_pandas()
        assert len(correlations) == 3

    def test_unit_family_validation_with_multiple_value_columns(self) -> None:
        """Test unit family validation works with multiple value columns."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "unc": [0.1, 0.2, 0.3, 0.4, 0.5] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        # Both columns have same unit family (MASS_CONCENTRATION)
        dataset = TimeSeriesDataset.from_dataframe(
            df, column_units={"conc": Unit.UG_M3, "unc": Unit.UG_M3}
        )

        # Should succeed - both columns have compatible families
        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols=["conc", "unc"],
            flag_col="flag",
            allow_missing_units=False,
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have 6 pairs (3 pairs x 2 value columns)
        assert len(result) == 6

    def test_unit_family_validation_with_grouped_correlation(self) -> None:
        """Test unit family validation works correctly with grouped correlation."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=20, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10 + ["site2"] * 10,
                "pollutant": (["PM25"] * 5 + ["PM10"] * 5) * 2,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 4,
                "flag": [QCFlag.VALID.value] * 20,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(
            df, column_units={"conc": Unit.UG_M3}
        )

        # Should succeed with grouping
        module = CorrelationModule(
            dataset=dataset,
            config={
                CorrelationConfig.GROUP_BY: ["site_id"],
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
                CorrelationConfig.ALLOW_MIXED_UNIT_FAMILIES: False,
            },
            
        )

        module.run(operations=[CorrelationOperation.PEARSON])

        correlations = module.results[CorrelationResult.CORRELATIONS]
        if isinstance(correlations, pl.DataFrame):
            correlations = correlations.to_pandas()

        # Should have 6 rows (3 pairs x 2 sites)
        assert len(correlations) == 6

    def test_unit_family_validation_skips_if_no_units(self, caplog) -> None:
        """Test validation is skipped if no units present (with override)."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        # No units
        dataset = TimeSeriesDataset.from_dataframe(df)

        module = CorrelationModule(
            dataset=dataset,
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
                CorrelationConfig.ALLOW_MISSING_UNITS: True,  # Allow no units
                CorrelationConfig.ALLOW_MIXED_UNIT_FAMILIES: False,
            },
            
        )

        module.run(operations=[CorrelationOperation.PEARSON])

        # Validation should be skipped silently (no unit family validation logs)
        unit_family_logs = [
            r for r in caplog.records if "Unit family validation" in r.message
        ]
        assert len(unit_family_logs) == 0

    def test_unit_family_validation_different_families_same_column_architecture(
        self,
    ) -> None:
        """Test that current architecture stores units at column level.

        This test documents that in the current design, all categories
        (e.g., PM2.5, NO2) within a single value column (e.g., 'conc')
        share the same unit. The validation checks the column's unit family,
        not per-category units.
        """
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["NO2"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        # In current architecture, all rows in 'conc' column share same unit
        # Both PM2.5 and NO2 would have ug/m3 (MASS_CONCENTRATION family)
        dataset = TimeSeriesDataset.from_dataframe(
            df, column_units={"conc": Unit.UG_M3}
        )

        # This should succeed because the column has a valid unit family
        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=False,
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        assert len(result) == 3  # PM25-PM25, PM25-NO2, NO2-NO2

    def test_unit_family_validation_string_unit_converted(self) -> None:
        """Test that string units are automatically converted to Unit enum."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        # Use string unit (will be converted to Unit enum)
        dataset = TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ug/m3"})

        module = CorrelationModule(
            dataset=dataset,
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
                CorrelationConfig.ALLOW_MISSING_UNITS: False,
                CorrelationConfig.ALLOW_MIXED_UNIT_FAMILIES: False,
            },
            
        )

        module.run(operations=[CorrelationOperation.PEARSON])

        # Should succeed (string unit converted to Unit enum)
        correlations = module.results[CorrelationResult.CORRELATIONS]
        if isinstance(correlations, pl.DataFrame):
            correlations = correlations.to_pandas()
        assert len(correlations) == 3

    def test_unit_family_validation_spearman_also_validates(self) -> None:
        """Test Spearman correlation also validates unit families."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(
            df, column_units={"conc": Unit.UG_M3}
        )

        # Spearman should also validate
        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="spearman",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=False,
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        assert len(result) == 3

    def test_unit_family_validation_default_behavior(self) -> None:
        """Test that unit family validation is OFF by default (backward compatibility)."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(
            df, column_units={"conc": Unit.UG_M3}
        )

        # Don't specify ALLOW_MIXED_UNIT_FAMILIES - should default to False
        module = CorrelationModule(
            dataset=dataset,
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
                # ALLOW_MIXED_UNIT_FAMILIES not specified
            },
            
        )

        module.run(operations=[CorrelationOperation.PEARSON])

        # Should succeed (validation happens but doesn't fail for compatible units)
        correlations = module.results[CorrelationResult.CORRELATIONS]
        assert len(correlations) == 3

    def test_mixed_unit_families_across_columns_raises_error(self) -> None:
        """Test that mixed unit families across value columns raises error by default."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "temp": [20.0, 21.0, 22.0, 23.0, 24.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        # conc: MASS_CONCENTRATION, temp: VOLUME_CONCENTRATION (different families)
        dataset = TimeSeriesDataset.from_dataframe(
            df, column_units={"conc": Unit.UG_M3, "temp": Unit.PPB}
        )

        # Should raise error - different unit families (test via module)
        from air_quality.exceptions import UnitError

        with pytest.raises(UnitError, match="different unit families"):
            module = CorrelationModule(
                dataset=dataset,
                config={
                    CorrelationConfig.GROUP_BY: None,
                    CorrelationConfig.CATEGORY_COL: "pollutant",
                    CorrelationConfig.VALUE_COLS: ["conc", "temp"],
                    CorrelationConfig.FLAG_COL: "flag",
                    CorrelationConfig.ALLOW_MISSING_UNITS: False,
                    CorrelationConfig.ALLOW_MIXED_UNIT_FAMILIES: False,  # Default, but explicit
                },
                
            )
            module.run(operations=[CorrelationOperation.PEARSON])

    def test_mixed_unit_families_with_override_succeeds(self) -> None:
        """Test that ALLOW_MIXED_UNIT_FAMILIES override allows mixed families."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "temp": [20.0, 21.0, 22.0, 23.0, 24.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        # conc: MASS_CONCENTRATION, temp: VOLUME_CONCENTRATION (different families)
        dataset = TimeSeriesDataset.from_dataframe(
            df, column_units={"conc": Unit.UG_M3, "temp": Unit.PPB}
        )

        # Should succeed with override
        module = CorrelationModule(
            dataset=dataset,
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: ["conc", "temp"],
                CorrelationConfig.FLAG_COL: "flag",
                CorrelationConfig.ALLOW_MISSING_UNITS: False,
                CorrelationConfig.ALLOW_MIXED_UNIT_FAMILIES: True,  # Override
            },
            
        )

        module.run(operations=[CorrelationOperation.PEARSON])

        # Should succeed and produce results
        correlations = module.results[CorrelationResult.CORRELATIONS]
        if isinstance(correlations, pl.DataFrame):
            correlations = correlations.to_pandas()

        # Should have 6 pairs (3 pairs x 2 value columns)
        assert len(correlations) == 6

    def test_same_family_different_units_across_columns_succeeds(self) -> None:
        """Test that same family with different units (e.g., ug/m3 and mg/m3) succeeds."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "unc": [0.1, 0.2, 0.3, 0.4, 0.5] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        # Both MASS_CONCENTRATION but different scales
        dataset = TimeSeriesDataset.from_dataframe(
            df, column_units={"conc": Unit.UG_M3, "unc": Unit.MG_M3}
        )

        # Should succeed - same family
        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols=["conc", "unc"],
            flag_col="flag",
            allow_missing_units=False,
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have 6 pairs
        assert len(result) == 6

    def test_single_value_column_always_passes(self) -> None:
        """Test that single value column always passes family validation."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(
            df, column_units={"conc": Unit.UG_M3}
        )

        # Single column - no cross-column comparison needed
        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",  # Single column
            flag_col="flag",
            allow_missing_units=False,
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        assert len(result) == 3
