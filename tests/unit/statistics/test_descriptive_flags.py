"""Tests for QC flag filtering and count tracking in descriptive statistics.

Test ID: T021
Module: air_quality.analysis.descriptive
Focus: QC flag filtering, count validation (n_total, n_valid, n_missing)
"""

import pandas as pd
import polars as pl
import pytest

from air_quality.analysis.descriptive import compute_descriptives, StatisticType
from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.qc_flags import QCFlag


class TestDescriptiveFlagFiltering:
    """Test QC flag filtering and count tracking."""

    def test_exclude_invalid_flag(self):
        """Test that INVALID flags are excluded from computation."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=5, freq="h"),
                "site_id": ["S1"] * 5,
                "pollutant": ["PM25"] * 5,
                "conc": [1.0, 2.0, 999.0, 4.0, 5.0],
                "flag": [
                    QCFlag.VALID.value,
                    QCFlag.VALID.value,
                    QCFlag.INVALID.value,  # Should be excluded
                    QCFlag.VALID.value,
                    QCFlag.VALID.value,
                ],
            }
        )
        dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

        result = compute_descriptives(
            dataset=dataset,
            group_by=None,
            pollutant_col="pollutant",
            conc_col="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have correct counts
        assert (result["n_total"] == 5).all()
        assert (result["n_valid"] == 4).all()
        assert (result["n_missing"] == 1).all()

        # Mean should exclude the invalid value: (1+2+4+5)/4 = 3.0
        stats_dict = dict(zip(result["stat"], result["value"]))
        assert stats_dict[StatisticType.MEAN.value] == pytest.approx(3.0)

    def test_exclude_outlier_flag(self):
        """Test that OUTLIER flags are excluded from computation."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=5, freq="h"),
                "site_id": ["S1"] * 5,
                "pollutant": ["PM25"] * 5,
                "conc": [1.0, 2.0, 999.0, 4.0, 5.0],
                "flag": [
                    QCFlag.VALID.value,
                    QCFlag.VALID.value,
                    QCFlag.OUTLIER.value,  # Should be excluded
                    QCFlag.VALID.value,
                    QCFlag.VALID.value,
                ],
            }
        )
        dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

        result = compute_descriptives(
            dataset=dataset,
            group_by=None,
            pollutant_col="pollutant",
            conc_col="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have correct counts
        assert (result["n_total"] == 5).all()
        assert (result["n_valid"] == 4).all()
        assert (result["n_missing"] == 1).all()

        # Mean should exclude the outlier: (1+2+4+5)/4 = 3.0
        stats_dict = dict(zip(result["stat"], result["value"]))
        assert stats_dict[StatisticType.MEAN.value] == pytest.approx(3.0)

    def test_below_dl_treated_as_missing(self):
        """Test that BELOW_DL flags are treated as missing (excluded but counted)."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=5, freq="h"),
                "site_id": ["S1"] * 5,
                "pollutant": ["PM25"] * 5,
                "conc": [1.0, 2.0, 0.5, 4.0, 5.0],
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
            pollutant_col="pollutant",
            conc_col="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have correct counts
        assert (result["n_total"] == 5).all()
        assert (result["n_valid"] == 4).all()
        assert (result["n_missing"] == 1).all()

        # Mean should exclude below_dl: (1+2+4+5)/4 = 3.0
        stats_dict = dict(zip(result["stat"], result["value"]))
        assert stats_dict[StatisticType.MEAN.value] == pytest.approx(3.0)

    def test_mixed_flags(self):
        """Test handling of mixed QC flags."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=10, freq="h"),
                "site_id": ["S1"] * 10,
                "pollutant": ["PM25"] * 10,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "flag": [
                    QCFlag.VALID.value,
                    QCFlag.VALID.value,
                    QCFlag.BELOW_DL.value,
                    QCFlag.VALID.value,
                    QCFlag.INVALID.value,
                    QCFlag.VALID.value,
                    QCFlag.OUTLIER.value,
                    QCFlag.VALID.value,
                    QCFlag.VALID.value,
                    QCFlag.VALID.value,
                ],
            }
        )
        dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

        result = compute_descriptives(
            dataset=dataset,
            group_by=None,
            pollutant_col="pollutant",
            conc_col="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Valid: indices 0,1,3,5,7,8,9 = 7 values
        # Missing: indices 2,4,6 = 3 values (below_dl, invalid, outlier)
        assert (result["n_total"] == 10).all()
        assert (result["n_valid"] == 7).all()
        assert (result["n_missing"] == 3).all()

        # Mean should be (1+2+4+6+8+9+10)/7
        stats_dict = dict(zip(result["stat"], result["value"]))
        expected_mean = (1.0 + 2.0 + 4.0 + 6.0 + 8.0 + 9.0 + 10.0) / 7.0
        assert stats_dict[StatisticType.MEAN.value] == pytest.approx(expected_mean)

    def test_count_consistency(self):
        """Test that n_total = n_valid + n_missing always holds."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=20, freq="h"),
                "site_id": ["S1"] * 10 + ["S2"] * 10,
                "pollutant": ["PM25"] * 20,
                "conc": list(range(20)),
                "flag": [
                    QCFlag.VALID.value,
                    QCFlag.BELOW_DL.value,
                    QCFlag.VALID.value,
                    QCFlag.INVALID.value,
                    QCFlag.VALID.value,
                    QCFlag.OUTLIER.value,
                    QCFlag.VALID.value,
                    QCFlag.VALID.value,
                    QCFlag.BELOW_DL.value,
                    QCFlag.VALID.value,
                ]
                * 2,
            }
        )
        dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

        result = compute_descriptives(
            dataset=dataset,
            group_by=["site_id"],
            pollutant_col="pollutant",
            conc_col="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Check consistency for all rows
        assert (result["n_total"] == result["n_valid"] + result["n_missing"]).all()

    def test_no_flag_column_all_valid(self):
        """Test handling when flag column is missing (all treated as valid)."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=5, freq="h"),
                "site_id": ["S1"] * 5,
                "pollutant": ["PM25"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0],
                # No flag column
            }
        )
        dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

        result = compute_descriptives(
            dataset=dataset,
            group_by=None,
            pollutant_col="pollutant",
            conc_col="conc",
            flag_col="flag",  # Will be None/missing in dataset
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should treat all as valid
        assert (result["n_total"] == 5).all()
        assert (result["n_valid"] == 5).all()
        assert (result["n_missing"] == 0).all()

        # Mean should be (1+2+3+4+5)/5 = 3.0
        stats_dict = dict(zip(result["stat"], result["value"]))
        assert stats_dict[StatisticType.MEAN.value] == pytest.approx(3.0)

    def test_null_flags_treated_as_valid(self):
        """Test that null/None flag values are treated as VALID."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=5, freq="h"),
                "site_id": ["S1"] * 5,
                "pollutant": ["PM25"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0],
                "flag": [
                    QCFlag.VALID.value,
                    None,
                    QCFlag.VALID.value,
                    None,
                    QCFlag.VALID.value,
                ],
            }
        )
        dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

        result = compute_descriptives(
            dataset=dataset,
            group_by=None,
            pollutant_col="pollutant",
            conc_col="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # All should be treated as valid (including None flags)
        assert (result["n_total"] == 5).all()
        assert (result["n_valid"] == 5).all()
        assert (result["n_missing"] == 0).all()

    def test_counts_per_group(self):
        """Test that counts are computed correctly per group."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=10, freq="h"),
                "site_id": ["S1"] * 5 + ["S2"] * 5,
                "pollutant": ["PM25"] * 10,
                "conc": list(range(10)),
                "flag": [
                    QCFlag.VALID.value,
                    QCFlag.VALID.value,
                    QCFlag.INVALID.value,
                    QCFlag.VALID.value,
                    QCFlag.BELOW_DL.value,
                    # S2 flags
                    QCFlag.VALID.value,
                    QCFlag.OUTLIER.value,
                    QCFlag.VALID.value,
                    QCFlag.VALID.value,
                    QCFlag.VALID.value,
                ],
            }
        )
        dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

        result = compute_descriptives(
            dataset=dataset,
            group_by=["site_id"],
            pollutant_col="pollutant",
            conc_col="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # S1: 5 total, 3 valid (indices 0,1,3), 2 missing
        s1_rows = result[result["site_id"] == "S1"]
        assert (s1_rows["n_total"] == 5).all()
        assert (s1_rows["n_valid"] == 3).all()
        assert (s1_rows["n_missing"] == 2).all()

        # S2: 5 total, 4 valid (indices 5,7,8,9), 1 missing
        s2_rows = result[result["site_id"] == "S2"]
        assert (s2_rows["n_total"] == 5).all()
        assert (s2_rows["n_valid"] == 4).all()
        assert (s2_rows["n_missing"] == 1).all()

    def test_all_flags_excluded(self):
        """Test when all data is excluded by QC flags."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=5, freq="h"),
                "site_id": ["S1"] * 5,
                "pollutant": ["PM25"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0],
                "flag": [
                    QCFlag.INVALID.value,
                    QCFlag.OUTLIER.value,
                    QCFlag.BELOW_DL.value,
                    QCFlag.INVALID.value,
                    QCFlag.OUTLIER.value,
                ],
            }
        )
        dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

        result = compute_descriptives(
            dataset=dataset,
            group_by=None,
            pollutant_col="pollutant",
            conc_col="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have n_valid=0, all stats are NaN
        assert (result["n_total"] == 5).all()
        assert (result["n_valid"] == 0).all()
        assert (result["n_missing"] == 5).all()
        assert result["value"].isna().all()
