"""Tests for basic descriptive statistics computation.

Test ID: T019
Module: air_quality.analysis.descriptive
Focus: Basic single-site descriptive statistics
"""

import pandas as pd
import polars as pl
import pytest

from air_quality.analysis.descriptive import compute_descriptives, DescriptiveStatsOperation
from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.qc_flags import QCFlag


class TestBasicDescriptiveStats:
    """Test basic descriptive statistics on single-site data."""

    @pytest.fixture
    def simple_dataset(self) -> TimeSeriesDataset:
        """Create a simple single-site, single-pollutant dataset."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=10, freq="h"),
                "site_id": ["S1"] * 10,
                "pollutant": ["PM25"] * 10,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "flag": [QCFlag.VALID.value] * 10,
            }
        )
        return TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

    def test_compute_descriptives_returns_dataframe(self, simple_dataset):
        """Test that compute_descriptives returns a Polars or Pandas DataFrame."""
        result = compute_descriptives(
            dataset=simple_dataset,
            group_by=None,
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
        )

        # Should return a DataFrame (Polars or Pandas)
        assert isinstance(result, (pl.DataFrame, pd.DataFrame))

    def test_compute_descriptives_tidy_format(self, simple_dataset):
        """Test that results are in tidy format (one row per statistic)."""
        result = compute_descriptives(
            dataset=simple_dataset,
            group_by=None,
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have rows for each statistic
        expected_stats = {
            DescriptiveStatsOperation.MEAN.value,
            DescriptiveStatsOperation.MEDIAN.value,
            DescriptiveStatsOperation.STD.value,
            DescriptiveStatsOperation.MIN.value,
            DescriptiveStatsOperation.MAX.value,
            "q05",
            "q25",
            "q75",
            "q95",
        }
        assert set(result["stat"].values) == expected_stats

    def test_compute_descriptives_correct_values(self, simple_dataset):
        """Test that computed statistics match expected values."""
        result = compute_descriptives(
            dataset=simple_dataset,
            group_by=None,
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Create lookup dict for easy access
        stats_dict = dict(zip(result["stat"], result["value"]))

        # Check known statistics for [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert stats_dict[DescriptiveStatsOperation.MEAN.value] == pytest.approx(5.5)
        assert stats_dict[DescriptiveStatsOperation.MEDIAN.value] == pytest.approx(5.5)
        assert stats_dict[DescriptiveStatsOperation.MIN.value] == pytest.approx(1.0)
        assert stats_dict[DescriptiveStatsOperation.MAX.value] == pytest.approx(10.0)

    def test_compute_descriptives_has_counts(self, simple_dataset):
        """Test that results include n_total, n_valid, n_missing."""
        result = compute_descriptives(
            dataset=simple_dataset,
            group_by=None,
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have count columns
        assert "n_total" in result.columns
        assert "n_valid" in result.columns
        assert "n_missing" in result.columns

        # All statistics should have same counts
        assert (result["n_total"] == 10).all()
        assert (result["n_valid"] == 10).all()
        assert (result["n_missing"] == 0).all()

    def test_compute_descriptives_includes_pollutant(self, simple_dataset):
        """Test that results include pollutant identifier."""
        result = compute_descriptives(
            dataset=simple_dataset,
            group_by=None,
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have pollutant column
        assert "pollutant" in result.columns
        assert (result["pollutant"] == "PM25").all()

    def test_compute_descriptives_no_groups_global_summary(self, simple_dataset):
        """Test that with group_by=None, we get global summary."""
        result = compute_descriptives(
            dataset=simple_dataset,
            group_by=None,
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have exactly 9 rows (one per statistic) for one pollutant
        assert len(result) == 9

    def test_compute_descriptives_with_missing_data(self):
        """Test handling of missing values (NaN)."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=5, freq="h"),
                "site_id": ["S1"] * 5,
                "pollutant": ["PM25"] * 5,
                "conc": [1.0, 2.0, float("nan"), 4.0, 5.0],
                "flag": [
                    QCFlag.VALID.value,
                    QCFlag.VALID.value,
                    QCFlag.BELOW_DL.value,  # Treated as missing
                    QCFlag.VALID.value,
                    QCFlag.VALID.value,
                ],
            }
        )
        dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

        result = compute_descriptives(
            dataset=dataset,
            group_by=None,
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have correct counts
        assert (result["n_total"] == 5).all()
        assert (result["n_valid"] == 4).all()  # Excludes NaN row
        assert (result["n_missing"] == 1).all()

        # Mean should be (1+2+4+5)/4 = 3.0
        stats_dict = dict(zip(result["stat"], result["value"]))
        assert stats_dict[DescriptiveStatsOperation.MEAN.value] == pytest.approx(3.0)

    def test_compute_descriptives_excludes_invalid_outlier(self):
        """Test that invalid and outlier flags are excluded from computation."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=5, freq="h"),
                "site_id": ["S1"] * 5,
                "pollutant": ["PM25"] * 5,
                "conc": [1.0, 2.0, 999.0, 4.0, 5.0],  # 999 is outlier
                "flag": [
                    QCFlag.VALID.value,
                    QCFlag.VALID.value,
                    QCFlag.OUTLIER.value,
                    QCFlag.VALID.value,
                    QCFlag.INVALID.value,  # Should also be excluded
                ],
            }
        )
        dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

        result = compute_descriptives(
            dataset=dataset,
            group_by=None,
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should exclude outlier and invalid rows
        assert (result["n_total"] == 5).all()
        assert (result["n_valid"] == 3).all()  # Only rows 0, 1, 3
        assert (result["n_missing"] == 2).all()

        # Mean should be (1+2+4)/3 = 2.333...
        stats_dict = dict(zip(result["stat"], result["value"]))
        assert stats_dict[DescriptiveStatsOperation.MEAN.value] == pytest.approx(7.0 / 3.0)

    def test_compute_descriptives_empty_after_filtering(self):
        """Test handling when all data is filtered out."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=3, freq="h"),
                "site_id": ["S1"] * 3,
                "pollutant": ["PM25"] * 3,
                "conc": [1.0, 2.0, 3.0],
                "flag": [
                    QCFlag.INVALID.value,
                    QCFlag.OUTLIER.value,
                    QCFlag.BELOW_DL.value,
                ],
            }
        )
        dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

        result = compute_descriptives(
            dataset=dataset,
            group_by=None,
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should still have rows for each statistic
        assert len(result) == 9

        # But all values should be NaN (no valid data)
        assert result["value"].isna().all()
        assert (result["n_total"] == 3).all()
        assert (result["n_valid"] == 0).all()
        assert (result["n_missing"] == 3).all()
