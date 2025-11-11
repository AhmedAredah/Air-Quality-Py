"""Unit tests for Spearman rank correlation.

Tests rank-based correlation computation for non-parametric analysis.

Constitution References
-----------------------
- Section 5: QC flag filtering (exclude INVALID, OUTLIER)
- Section 11: Vectorized rank transformation and correlation
- Section 15: Method provenance tracking
"""

from __future__ import annotations

import pandas as pd
import polars as pl
import pytest

from air_quality.analysis.correlation import compute_pairwise
from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.qc_flags import QCFlag


class TestSpearmanCorrelation:
    """Test Spearman rank correlation functionality."""

    def test_spearman_monotonic_relationship(self) -> None:
        """Test Spearman on monotonic non-linear relationship."""
        # Create monotonic but non-linear data: y = x^2
        # Spearman should detect perfect monotonic relationship (r_s = 1.0)
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] + [1.0, 4.0, 9.0, 16.0, 25.0],  # x^2
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="spearman",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Check cross-correlation (perfect monotonic positive)
        pm10_pm25 = result[
            (result["var_x"] == "PM10") & (result["var_y"] == "PM25")
        ].iloc[0]
        assert pm10_pm25["correlation"] == pytest.approx(1.0, abs=1e-9)
        assert pm10_pm25["n"] == 5

    def test_spearman_vs_pearson_on_nonlinear(self) -> None:
        """Test Spearman detects monotonic relationship better than Pearson."""
        # Create exponential relationship
        import numpy as np

        x_vals = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_vals = [np.exp(x) for x in x_vals]

        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": x_vals + y_vals,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        # Spearman should be ~1.0 (perfect monotonic)
        result_spearman = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="spearman",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result_spearman, pl.DataFrame):
            result_spearman = result_spearman.to_pandas()

        pm10_pm25_spearman = result_spearman[
            (result_spearman["var_x"] == "PM10") & (result_spearman["var_y"] == "PM25")
        ].iloc[0]
        assert pm10_pm25_spearman["correlation"] == pytest.approx(1.0, abs=1e-9)

        # Pearson should be < 1.0 (not perfectly linear)
        result_pearson = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result_pearson, pl.DataFrame):
            result_pearson = result_pearson.to_pandas()

        pm10_pm25_pearson = result_pearson[
            (result_pearson["var_x"] == "PM10") & (result_pearson["var_y"] == "PM25")
        ].iloc[0]
        # Pearson should be high but not perfect (exponential relationship is not linear)
        # For y=exp(x) with x in [1,5], Pearson is ~0.886
        assert 0.80 < pm10_pm25_pearson["correlation"] < 1.0

    def test_spearman_rank_ties_handling(self) -> None:
        """Test Spearman handles tied ranks correctly."""
        # Create data with tied values
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=12, freq="h", tz="UTC"),
                "site_id": ["site1"] * 12,
                "pollutant": ["PM25"] * 6 + ["PM10"] * 6,
                "conc": [1.0, 2.0, 2.0, 3.0, 3.0, 3.0] * 2,  # Multiple ties
                "flag": [QCFlag.VALID.value] * 12,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="spearman",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Cross-correlation should be perfect (identical rank patterns)
        pm10_pm25 = result[
            (result["var_x"] == "PM10") & (result["var_y"] == "PM25")
        ].iloc[0]
        assert pm10_pm25["correlation"] == pytest.approx(1.0, abs=1e-9)
        assert pm10_pm25["n"] == 6

    def test_spearman_negative_monotonic(self) -> None:
        """Test Spearman on negative monotonic relationship."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0]
                + [25.0, 16.0, 9.0, 4.0, 1.0],  # Decreasing
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="spearman",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Check cross-correlation (perfect monotonic negative)
        pm10_pm25 = result[
            (result["var_x"] == "PM10") & (result["var_y"] == "PM25")
        ].iloc[0]
        assert pm10_pm25["correlation"] == pytest.approx(-1.0, abs=1e-9)
        assert pm10_pm25["n"] == 5

    def test_spearman_diagonal_always_one(self) -> None:
        """Test Spearman diagonal (self-correlation) is always 1.0."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.5, 2.3, 3.1, 4.7, 5.9] * 2,  # Arbitrary values
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="spearman",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Check both diagonal entries
        pm10_pm10 = result[
            (result["var_x"] == "PM10") & (result["var_y"] == "PM10")
        ].iloc[0]
        assert pm10_pm10["correlation"] == pytest.approx(1.0, abs=1e-9)

        pm25_pm25 = result[
            (result["var_x"] == "PM25") & (result["var_y"] == "PM25")
        ].iloc[0]
        assert pm25_pm25["correlation"] == pytest.approx(1.0, abs=1e-9)

    def test_spearman_qc_flag_filtering(self) -> None:
        """Test Spearman respects QC flag filtering."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=14, freq="h", tz="UTC"),
                "site_id": ["site1"] * 14,
                "pollutant": ["PM25"] * 7 + ["PM10"] * 7,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0] * 2,
                "flag": (
                    [QCFlag.VALID.value] * 3
                    + [QCFlag.INVALID.value] * 2  # Exclude
                    + [QCFlag.VALID.value] * 2
                    + [QCFlag.VALID.value] * 7
                ),
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="spearman",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # PM25 should have 5 valid observations (3 + 2)
        pm25_pm25 = result[
            (result["var_x"] == "PM25") & (result["var_y"] == "PM25")
        ].iloc[0]
        assert pm25_pm25["n"] == 5

        # PM10 should have 7 valid observations
        pm10_pm10 = result[
            (result["var_x"] == "PM10") & (result["var_y"] == "PM10")
        ].iloc[0]
        assert pm10_pm10["n"] == 7

    def test_spearman_output_schema_matches_pearson(self) -> None:
        """Test Spearman output has same schema as Pearson."""
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

        result_pearson = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        result_spearman = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="spearman",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        # Convert to pandas for schema comparison
        if isinstance(result_pearson, pl.DataFrame):
            result_pearson = result_pearson.to_pandas()
        if isinstance(result_spearman, pl.DataFrame):
            result_spearman = result_spearman.to_pandas()

        # Same columns
        assert list(result_pearson.columns) == list(result_spearman.columns)

        # Same number of rows (same pairs)
        assert len(result_pearson) == len(result_spearman)

        # Same var_x, var_y pairs
        pearson_pairs = set(zip(result_pearson["var_x"], result_pearson["var_y"]))
        spearman_pairs = set(zip(result_spearman["var_x"], result_spearman["var_y"]))
        assert pearson_pairs == spearman_pairs

    def test_spearman_constant_values_returns_nan(self) -> None:
        """Test Spearman with constant values returns NaN (no variance)."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [5.0] * 5 + [1.0, 2.0, 3.0, 4.0, 5.0],  # PM25 is constant
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="spearman",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Cross-correlation should be NaN (no variance in PM25 ranks)
        pm10_pm25 = result[
            (result["var_x"] == "PM10") & (result["var_y"] == "PM25")
        ].iloc[0]
        assert pd.isna(pm10_pm25["correlation"])
        assert pm10_pm25["n"] == 5
