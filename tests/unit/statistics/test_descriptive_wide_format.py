"""Tests for wide format output in descriptive statistics.

Test ID: T060
Module: air_quality.analysis.descriptive
Focus: Wide format output (one row per group with separate stat columns)
"""

import pandas as pd
import polars as pl
import pytest

from air_quality.analysis.descriptive import compute_descriptives, OutputFormat
from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.qc_flags import QCFlag


class TestWideFormatOutput:
    """Test wide format output for descriptive statistics."""

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

    @pytest.fixture
    def multi_site_dataset(self) -> TimeSeriesDataset:
        """Create a multi-site, multi-pollutant dataset."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=20, freq="h"),
                "site_id": ["S1"] * 10 + ["S2"] * 10,
                "pollutant": ["PM25"] * 5 + ["O3"] * 5 + ["PM25"] * 5 + ["O3"] * 5,
                "conc": list(range(1, 11)) + list(range(11, 21)),
                "flag": [QCFlag.VALID.value] * 20,
            }
        )
        return TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

    def test_wide_format_returns_dataframe(self, simple_dataset):
        """Test that wide format returns a DataFrame."""
        result = compute_descriptives(
            dataset=simple_dataset,
            category_col="pollutant",
            value_cols="conc",
            output_format=OutputFormat.WIDE,
        )

        assert isinstance(result, (pl.DataFrame, pd.DataFrame))

    def test_wide_format_has_stat_columns(self, simple_dataset):
        """Test that wide format has separate columns for each statistic."""
        result = compute_descriptives(
            dataset=simple_dataset,
            category_col="pollutant",
            value_cols="conc",
            output_format=OutputFormat.WIDE,
        )

        # Should have columns for each statistic
        expected_stat_cols = ["mean", "median", "std", "min", "max", "q05", "q25", "q75", "q95"]
        for stat_col in expected_stat_cols:
            assert stat_col in result.columns, f"Missing stat column: {stat_col}"

    def test_wide_format_one_row_per_group(self, simple_dataset):
        """Test that wide format has one row per group (not 9 rows like tidy format)."""
        result = compute_descriptives(
            dataset=simple_dataset,
            category_col="pollutant",
            value_cols="conc",
            output_format=OutputFormat.WIDE,
        )

        # Single pollutant, single value_col -> 1 row (not 9)
        assert result.height == 1

    def test_wide_format_no_stat_column(self, simple_dataset):
        """Test that wide format does NOT have a 'stat' column."""
        result = compute_descriptives(
            dataset=simple_dataset,
            category_col="pollutant",
            value_cols="conc",
            output_format=OutputFormat.WIDE,
        )

        # Should NOT have 'stat' column (that's tidy format)
        assert "stat" not in result.columns

    def test_wide_format_correct_values(self, simple_dataset):
        """Test that wide format computes correct statistic values."""
        result = compute_descriptives(
            dataset=simple_dataset,
            category_col="pollutant",
            value_cols="conc",
            output_format=OutputFormat.WIDE,
        )

        # Extract first row
        row = result.to_dicts()[0]

        # Expected statistics for [1.0, 2.0, ..., 10.0]
        assert row["mean"] == pytest.approx(5.5, rel=1e-6)
        assert row["median"] == pytest.approx(5.5, rel=1e-6)
        assert row["min"] == pytest.approx(1.0, rel=1e-6)
        assert row["max"] == pytest.approx(10.0, rel=1e-6)

    def test_wide_format_has_count_columns(self, simple_dataset):
        """Test that wide format includes n_total, n_valid, n_missing."""
        result = compute_descriptives(
            dataset=simple_dataset,
            category_col="pollutant",
            value_cols="conc",
            output_format=OutputFormat.WIDE,
        )

        # Should have count columns
        assert "n_total" in result.columns
        assert "n_valid" in result.columns
        assert "n_missing" in result.columns

        row = result.to_dicts()[0]
        assert row["n_total"] == 10
        assert row["n_valid"] == 10
        assert row["n_missing"] == 0

    def test_wide_format_with_grouping(self, multi_site_dataset):
        """Test that wide format works with grouping."""
        result = compute_descriptives(
            dataset=multi_site_dataset,
            group_by=["site_id"],
            category_col="pollutant",
            value_cols="conc",
            output_format=OutputFormat.WIDE,
        )

        # 2 sites * 2 pollutants = 4 rows
        assert result.height == 4

        # Should have site_id column
        assert "site_id" in result.columns

        # Should have stat columns
        assert "mean" in result.columns
        assert "median" in result.columns

    def test_wide_format_with_multiple_value_cols(self, simple_dataset):
        """Test that wide format works with multiple value columns."""
        # Create dataset with multiple numeric columns
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=10, freq="h"),
                "site_id": ["S1"] * 10,
                "pollutant": ["PM25"] * 10,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "temp": [20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0],
                "flag": [QCFlag.VALID.value] * 10,
            }
        )
        dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

        result = compute_descriptives(
            dataset=dataset,
            category_col="pollutant",
            value_cols=["conc", "temp"],
            output_format=OutputFormat.WIDE,
        )

        # 1 pollutant * 2 value_cols = 2 rows
        assert result.height == 2

        # Should have value_col_name column
        assert "value_col_name" in result.columns

        # Check that both value columns are present
        value_col_names = result.select("value_col_name").to_series().to_list()
        assert "conc" in value_col_names
        assert "temp" in value_col_names

    def test_wide_format_preserves_category_col(self, simple_dataset):
        """Test that wide format preserves the category column."""
        result = compute_descriptives(
            dataset=simple_dataset,
            category_col="pollutant",
            value_cols="conc",
            output_format=OutputFormat.WIDE,
        )

        # Should have pollutant column
        assert "pollutant" in result.columns

        row = result.to_dicts()[0]
        assert row["pollutant"] == "PM25"

    def test_tidy_format_is_default(self, simple_dataset):
        """Test that TIDY format is the default (backward compatibility)."""
        result = compute_descriptives(
            dataset=simple_dataset,
            category_col="pollutant",
            value_cols="conc",
            # No output_format specified -> should default to TIDY
        )

        # Tidy format has 'stat' column
        assert "stat" in result.columns

        # Tidy format has 9 rows (one per statistic)
        assert result.height == 9

    def test_wide_vs_tidy_same_values(self, simple_dataset):
        """Test that wide and tidy formats compute the same values."""
        tidy_result = compute_descriptives(
            dataset=simple_dataset,
            category_col="pollutant",
            value_cols="conc",
            output_format=OutputFormat.TIDY,
        )

        wide_result = compute_descriptives(
            dataset=simple_dataset,
            category_col="pollutant",
            value_cols="conc",
            output_format=OutputFormat.WIDE,
        )

        # Extract mean from tidy format
        tidy_mean = tidy_result.filter(pl.col("stat") == "mean").select("value")[0, 0]

        # Extract mean from wide format
        wide_mean = wide_result.select("mean")[0, 0]

        # Should be the same
        assert tidy_mean == pytest.approx(wide_mean, rel=1e-10)

    def test_wide_format_with_no_category_col(self, simple_dataset):
        """Test that wide format works without category column (global stats)."""
        result = compute_descriptives(
            dataset=simple_dataset,
            category_col=None,
            value_cols="conc",
            output_format=OutputFormat.WIDE,
        )

        # Single value_col, no category -> 1 row
        assert result.height == 1

        # Should have stat columns
        assert "mean" in result.columns
        assert "median" in result.columns

        # Should NOT have category column
        assert "pollutant" not in result.columns
