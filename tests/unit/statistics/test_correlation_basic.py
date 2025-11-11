"""Unit tests for basic Pearson correlation.

Tests global (ungrouped) correlation analysis on two pollutants.

Constitution References
-----------------------
- Section 5: QC flag filtering (exclude INVALID, OUTLIER)
- Section 11: Vectorized correlation computation
- Section 15: Provenance tracking
"""

from __future__ import annotations

import pandas as pd
import polars as pl
import pytest

from air_quality.analysis.correlation import compute_pairwise
from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.qc_flags import QCFlag


class TestBasicPearsonCorrelation:
    """Test basic Pearson correlation functionality."""

    def test_perfect_positive_correlation(self) -> None:
        """Test perfect positive correlation (r = 1.0)."""
        # Create synthetic data: y = x (perfect linear relationship)
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,  # Same values for both
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        # Convert to pandas for easier assertions
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have 3 pairs: (PM10, PM10), (PM10, PM25), (PM25, PM25)
        assert len(result) == 3

        # Check diagonal (self-correlation = 1.0)
        pm10_pm10 = result[
            (result["var_x"] == "PM10") & (result["var_y"] == "PM10")
        ].iloc[0]
        assert pm10_pm10["correlation"] == pytest.approx(1.0, abs=1e-9)
        assert pm10_pm10["n"] == 5

        pm25_pm25 = result[
            (result["var_x"] == "PM25") & (result["var_y"] == "PM25")
        ].iloc[0]
        assert pm25_pm25["correlation"] == pytest.approx(1.0, abs=1e-9)
        assert pm25_pm25["n"] == 5

        # Check cross-correlation (perfect positive)
        pm10_pm25 = result[
            (result["var_x"] == "PM10") & (result["var_y"] == "PM25")
        ].iloc[0]
        assert pm10_pm25["correlation"] == pytest.approx(1.0, abs=1e-9)
        assert pm10_pm25["n"] == 5

    def test_perfect_negative_correlation(self) -> None:
        """Test perfect negative correlation (r = -1.0)."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0]
                + [5.0, 4.0, 3.0, 2.0, 1.0],  # Opposite
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Check cross-correlation (perfect negative)
        pm10_pm25 = result[
            (result["var_x"] == "PM10") & (result["var_y"] == "PM25")
        ].iloc[0]
        assert pm10_pm25["correlation"] == pytest.approx(-1.0, abs=1e-9)
        assert pm10_pm25["n"] == 5

    def test_zero_correlation(self) -> None:
        """Test zero correlation (r ≈ 0)."""
        # Create uncorrelated random data
        import numpy as np

        np.random.seed(42)

        df = pd.DataFrame(
            {
                "datetime": pd.date_range(
                    "2023-01-01", periods=200, freq="h", tz="UTC"
                ),
                "site_id": ["site1"] * 200,
                "pollutant": ["PM25"] * 100 + ["PM10"] * 100,
                "conc": list(np.random.randn(100)) + list(np.random.randn(100)),
                "flag": [QCFlag.VALID.value] * 200,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Check cross-correlation (should be near zero)
        pm10_pm25 = result[
            (result["var_x"] == "PM10") & (result["var_y"] == "PM25")
        ].iloc[0]
        # Allow wide tolerance for random data
        assert abs(pm10_pm25["correlation"]) < 0.2
        assert pm10_pm25["n"] == 100

    def test_ordered_pairs_var_x_le_var_y(self) -> None:
        """Test that pairs are ordered: var_x <= var_y."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=15, freq="h", tz="UTC"),
                "site_id": ["site1"] * 15,
                "pollutant": ["CO"] * 5 + ["NO2"] * 5 + ["O3"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 3,
                "flag": [QCFlag.VALID.value] * 15,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have 6 pairs: (CO,CO), (CO,NO2), (CO,O3), (NO2,NO2), (NO2,O3), (O3,O3)
        assert len(result) == 6

        # Check ordering: var_x <= var_y alphabetically
        for _, row in result.iterrows():
            assert (
                row["var_x"] <= row["var_y"]
            ), f"Pair ordering violated: {row['var_x']} > {row['var_y']}"

    def test_diagonal_included(self) -> None:
        """Test that diagonal (self-correlation) is included."""
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

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Check diagonal entries exist
        pm10_pm10 = result[(result["var_x"] == "PM10") & (result["var_y"] == "PM10")]
        assert len(pm10_pm10) == 1
        assert pm10_pm10.iloc[0]["correlation"] == pytest.approx(1.0, abs=1e-9)

        pm25_pm25 = result[(result["var_x"] == "PM25") & (result["var_y"] == "PM25")]
        assert len(pm25_pm25) == 1
        assert pm25_pm25.iloc[0]["correlation"] == pytest.approx(1.0, abs=1e-9)

    def test_qc_flag_filtering_excludes_invalid_outlier(self) -> None:
        """Test that INVALID and OUTLIER flags are excluded from correlation."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=15, freq="h", tz="UTC"),
                "site_id": ["site1"] * 15,
                "pollutant": ["PM25"] * 10 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 3,
                "flag": (
                    [QCFlag.VALID.value] * 3
                    + [QCFlag.INVALID.value] * 2  # Exclude
                    + [QCFlag.OUTLIER.value] * 2  # Exclude
                    + [QCFlag.VALID.value] * 3
                    + [QCFlag.VALID.value] * 5
                ),
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # PM25 should have only 6 valid observations (3 + 3)
        pm25_pm25 = result[
            (result["var_x"] == "PM25") & (result["var_y"] == "PM25")
        ].iloc[0]
        assert pm25_pm25["n"] == 6

        # PM10 should have 5 valid observations
        pm10_pm10 = result[
            (result["var_x"] == "PM10") & (result["var_y"] == "PM10")
        ].iloc[0]
        assert pm10_pm10["n"] == 5

    def test_below_dl_treated_as_missing(self) -> None:
        """Test that BELOW_DL flags are treated as missing (excluded from n)."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=12, freq="h", tz="UTC"),
                "site_id": ["site1"] * 12,
                "pollutant": ["PM25"] * 6 + ["PM10"] * 6,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0] * 2,
                "flag": (
                    [QCFlag.VALID.value] * 3
                    + [QCFlag.BELOW_DL.value] * 3  # Missing
                    + [QCFlag.VALID.value] * 6
                ),
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # PM25 should have only 3 valid observations
        pm25_pm25 = result[
            (result["var_x"] == "PM25") & (result["var_y"] == "PM25")
        ].iloc[0]
        assert pm25_pm25["n"] == 3

        # PM10 should have 6 valid observations
        pm10_pm10 = result[
            (result["var_x"] == "PM10") & (result["var_y"] == "PM10")
        ].iloc[0]
        assert pm10_pm10["n"] == 6

    def test_single_pollutant_returns_diagonal_only(self) -> None:
        """Test correlation with single pollutant returns only diagonal."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=5, freq="h", tz="UTC"),
                "site_id": ["site1"] * 5,
                "pollutant": ["PM25"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0],
                "flag": [QCFlag.VALID.value] * 5,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have only 1 pair: (PM25, PM25)
        assert len(result) == 1
        assert result.iloc[0]["var_x"] == "PM25"
        assert result.iloc[0]["var_y"] == "PM25"
        assert result.iloc[0]["correlation"] == pytest.approx(1.0, abs=1e-9)
        assert result.iloc[0]["n"] == 5

    def test_min_samples_threshold(self) -> None:
        """Test that pairs with < min_samples are excluded or flagged."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=8, freq="h", tz="UTC"),
                "site_id": ["site1"] * 8,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 3,  # PM10 has only 3 samples
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
                "flag": [QCFlag.VALID.value] * 8,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        # With min_samples=3, both pollutants should be included
        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            min_samples=3,
            allow_missing_units=True,
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have 3 pairs: (PM10, PM10), (PM10, PM25), (PM25, PM25)
        assert len(result) == 3

        # With min_samples=5, PM10 should be excluded (only 3 samples)
        result_strict = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            min_samples=5,
            allow_missing_units=True,
        )

        if isinstance(result_strict, pl.DataFrame):
            result_strict = result_strict.to_pandas()

        # Should have only 1 pair: (PM25, PM25)
        assert len(result_strict) == 1
        assert result_strict.iloc[0]["var_x"] == "PM25"
        assert result_strict.iloc[0]["var_y"] == "PM25"
