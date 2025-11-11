"""Tests for wide format output in correlation analysis.

Test ID: T061
Module: air_quality.analysis.correlation
Focus: Wide format output (correlation matrix with var_y as columns)
"""

import pandas as pd
import polars as pl
import pytest

from air_quality.analysis.correlation import compute_pairwise, OutputFormat
from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.qc_flags import QCFlag


class TestWideFormatCorrelation:
    """Test wide format output for correlation analysis."""

    @pytest.fixture
    def simple_dataset(self) -> TimeSeriesDataset:
        """Create a simple dataset with multiple pollutants."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=20, freq="h"),
                "site_id": ["S1"] * 20,
                "pollutant": ["PM25"] * 10 + ["O3"] * 10,
                "conc": list(range(1, 11)) + list(range(11, 21)),
                "flag": [QCFlag.VALID.value] * 20,
            }
        )
        return TimeSeriesDataset.from_dataframe(
            df, time_index_name="datetime", column_units={"conc": "ug/m3"}
        )

    def test_wide_format_returns_dataframe(self, simple_dataset):
        """Test that wide format returns a DataFrame."""
        result = compute_pairwise(
            dataset=simple_dataset,
            group_by=None,
            value_cols="conc",
            output_format=OutputFormat.WIDE,
        )

        assert isinstance(result, (pl.DataFrame, pd.DataFrame))

    def test_wide_format_creates_matrix_structure(self, simple_dataset):
        """Test that wide format creates matrix with var_y as columns."""
        result = compute_pairwise(
            dataset=simple_dataset,
            group_by=None,
            value_cols="conc",
            output_format=OutputFormat.WIDE,
        )

        # Should have columns for each unique pollutant
        assert "O3" in result.columns
        assert "PM25" in result.columns
        # Should have var_x as row identifier
        assert "var_x" in result.columns

    def test_wide_format_one_row_per_var_x(self, simple_dataset):
        """Test that wide format has one row per var_x value."""
        result = compute_pairwise(
            dataset=simple_dataset,
            group_by=None,
            value_cols="conc",
            output_format=OutputFormat.WIDE,
        )

        # 2 pollutants -> 2 rows (one per var_x)
        assert result.height == 2

    def test_wide_format_no_var_y_column(self, simple_dataset):
        """Test that wide format does NOT have a 'var_y' column."""
        result = compute_pairwise(
            dataset=simple_dataset,
            group_by=None,
            value_cols="conc",
            output_format=OutputFormat.WIDE,
        )

        # Should NOT have 'var_y' column (that's tidy format)
        assert "var_y" not in result.columns

    def test_wide_format_diagonal_values(self, simple_dataset):
        """Test that diagonal entries (self-correlation) are 1.0."""
        result = compute_pairwise(
            dataset=simple_dataset,
            group_by=None,
            value_cols="conc",
            output_format=OutputFormat.WIDE,
        )

        # Get PM25-PM25 correlation (diagonal)
        pm25_row = result.filter(pl.col("var_x") == "PM25")
        pm25_self_corr = pm25_row.select("PM25")[0, 0]

        assert pm25_self_corr == pytest.approx(1.0, abs=1e-6)

    def test_tidy_format_is_default(self, simple_dataset):
        """Test that TIDY format is the default (backward compatibility)."""
        result = compute_pairwise(
            dataset=simple_dataset,
            group_by=None,
            value_cols="conc",
            # No output_format specified -> should default to TIDY
        )

        # Tidy format has 'var_y' column
        assert "var_y" in result.columns

        # Tidy format has 3 rows for 2 pollutants: (O3,O3), (O3,PM25), (PM25,PM25)
        assert result.height == 3

    def test_wide_vs_tidy_same_values(self, simple_dataset):
        """Test that wide and tidy formats contain the same correlation values."""
        tidy_result = compute_pairwise(
            dataset=simple_dataset,
            group_by=None,
            value_cols="conc",
            output_format=OutputFormat.TIDY,
        )

        wide_result = compute_pairwise(
            dataset=simple_dataset,
            group_by=None,
            value_cols="conc",
            output_format=OutputFormat.WIDE,
        )

        # Extract O3-PM25 correlation from tidy format
        tidy_cross_corr = tidy_result.filter(
            (pl.col("var_x") == "O3") & (pl.col("var_y") == "PM25")
        ).select("correlation")[0, 0]

        # Extract O3-PM25 correlation from wide format (row O3, column PM25)
        wide_cross_corr = wide_result.filter(pl.col("var_x") == "O3").select("PM25")[0, 0]

        # Should be the same
        assert tidy_cross_corr == pytest.approx(wide_cross_corr, abs=1e-10)

    def test_wide_format_with_multiple_value_cols(self, simple_dataset):
        """Test that wide format works with multiple value columns."""
        # Create dataset with two numeric columns
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=20, freq="h"),
                "site_id": ["S1"] * 20,
                "pollutant": ["PM25"] * 10 + ["O3"] * 10,
                "conc": list(range(1, 11)) + list(range(11, 21)),
                "unc": [x * 0.1 for x in range(1, 21)],
                "flag": [QCFlag.VALID.value] * 20,
            }
        )
        dataset = TimeSeriesDataset.from_dataframe(
            df, time_index_name="datetime", column_units={"conc": "ug/m3", "unc": "ug/m3"}
        )

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            value_cols=["conc", "unc"],
            output_format=OutputFormat.WIDE,
        )

        # Should have value_col_name column
        assert "value_col_name" in result.columns

        # Should have 2 value columns * 2 pollutants = 4 rows
        assert result.height == 4

        # Check that both value columns are present
        value_col_names = result.select("value_col_name").unique().to_series().to_list()
        assert "conc" in value_col_names
        assert "unc" in value_col_names
