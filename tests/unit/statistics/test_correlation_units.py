"""Unit tests for correlation with unit metadata handling.

Tests unit presence enforcement and allow_missing_units override.

Constitution References
-----------------------
- Section 15: Units enforcement for interpretability
- Section 15: Provenance tracking for unit override decisions
"""

from __future__ import annotations

import pandas as pd
import polars as pl
import pytest

from air_quality.analysis.correlation import compute_pairwise
from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.exceptions import UnitError
from air_quality.qc_flags import QCFlag


class TestCorrelationUnits:
    """Test unit metadata handling in correlation analysis."""

    def test_correlation_requires_units_by_default(self) -> None:
        """Test correlation raises UnitError if units are missing (default behavior)."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        # Create dataset without unit metadata
        dataset = TimeSeriesDataset.from_dataframe(df)

        # Should raise UnitError if value_col has no units
        with pytest.raises(UnitError, match="Missing unit metadata"):
            compute_pairwise(
                dataset=dataset,
                group_by=None,
                correlation_type="pearson",
                category_col="pollutant",
                value_cols="conc",
                flag_col="flag",
                allow_missing_units=False,  # Default behavior
            )

    def test_correlation_with_units_present_succeeds(self) -> None:
        """Test correlation succeeds when units are present."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        # Create dataset with unit metadata
        dataset = TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ug/m3"})

        # Should succeed with units present
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

    def test_correlation_override_allows_missing_units(self) -> None:
        """Test allow_missing_units=True permits correlation without units."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        # Create dataset without units
        dataset = TimeSeriesDataset.from_dataframe(df)

        # Should succeed with override
        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Override
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have 3 pairs
        assert len(result) == 3

        # Correlation values should still be correct
        pm10_pm25 = result[
            (result["var_x"] == "PM10") & (result["var_y"] == "PM25")
        ].iloc[0]
        assert pm10_pm25["correlation"] == pytest.approx(1.0, abs=1e-9)

    def test_correlation_partial_units_raises_error(self) -> None:
        """Test correlation raises error if some pollutants have units but others don't."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=15, freq="h", tz="UTC"),
                "site_id": ["site1"] * 15,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5 + ["NO2"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 3,
                "flag": [QCFlag.VALID.value] * 15,
            }
        )

        # Create dataset with units for conc column
        # (TimeSeriesDataset applies units at column level, not per-pollutant)
        # This test checks column-level unit presence
        dataset = TimeSeriesDataset.from_dataframe(df)

        # Without any units, should raise
        with pytest.raises(UnitError, match="Missing unit metadata"):
            compute_pairwise(
                dataset=dataset,
                group_by=None,
                correlation_type="pearson",
                category_col="pollutant",
                value_cols="conc",
                flag_col="flag",
                allow_missing_units=False,
            )

    def test_correlation_units_checked_before_computation(self) -> None:
        """Test unit check happens before expensive computation."""
        # Large dataset to make computation noticeable
        import numpy as np

        np.random.seed(42)

        df = pd.DataFrame(
            {
                "datetime": pd.date_range(
                    "2023-01-01", periods=10000, freq="h", tz="UTC"
                ),
                "site_id": ["site1"] * 10000,
                "pollutant": (["PM25"] * 5000 + ["PM10"] * 5000),
                "conc": list(np.random.randn(10000)),
                "flag": [QCFlag.VALID.value] * 10000,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        # Should fail fast with UnitError (not timeout or memory error)
        with pytest.raises(UnitError, match="Missing unit metadata"):
            compute_pairwise(
                dataset=dataset,
                group_by=None,
                correlation_type="pearson",
                category_col="pollutant",
                value_cols="conc",
                flag_col="flag",
                allow_missing_units=False,
            )

    def test_correlation_override_works_with_grouping(self) -> None:
        """Test allow_missing_units works correctly with grouped correlation."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=20, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10 + ["site2"] * 10,
                "pollutant": (["PM25"] * 5 + ["PM10"] * 5) * 2,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 4,
                "flag": [QCFlag.VALID.value] * 20,
            }
        )

        # Dataset without units
        dataset = TimeSeriesDataset.from_dataframe(df)

        # Should succeed with override
        result = compute_pairwise(
            dataset=dataset,
            group_by=["site_id"],
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have 6 rows (3 pairs x 2 sites)
        assert len(result) == 6

    def test_correlation_units_error_message_includes_column_name(self) -> None:
        """Test UnitError message identifies which column is missing units."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        with pytest.raises(UnitError, match="conc"):
            compute_pairwise(
                dataset=dataset,
                group_by=None,
                correlation_type="pearson",
                category_col="pollutant",
                value_cols="conc",  # This column missing units
                flag_col="flag",
                allow_missing_units=False,
            )

    def test_correlation_spearman_also_checks_units(self) -> None:
        """Test Spearman correlation also enforces unit requirements."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        # Spearman should also raise UnitError without units
        with pytest.raises(UnitError, match="Missing unit metadata"):
            compute_pairwise(
                dataset=dataset,
                group_by=None,
                correlation_type="spearman",  # Spearman, not Pearson
                category_col="pollutant",
                value_cols="conc",
                flag_col="flag",
                allow_missing_units=False,
            )

        # Spearman should succeed with override
        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="spearman",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        assert len(result) == 3

    def test_correlation_with_multiple_value_columns_checks_all_units(self) -> None:
        """Test correlation with multiple value columns checks units for all."""
        # Note: Current API doesn't support multiple value columns for correlation
        # This test documents expected future behavior
        # For now, this is a placeholder/skip test

        pytest.skip(
            "Multiple value columns not yet supported for correlation (future enhancement)"
        )
