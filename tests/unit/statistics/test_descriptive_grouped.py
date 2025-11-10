"""Tests for grouped descriptive statistics computation.

Test ID: T020
Module: air_quality.analysis.descriptive
Focus: Grouping by site_id and multi-pollutant support
"""

import pandas as pd
import polars as pl
import pytest

from air_quality.analysis.descriptive import compute_descriptives, StatisticType
from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.qc_flags import QCFlag


class TestGroupedDescriptiveStats:
    """Test descriptive statistics with grouping."""

    @pytest.fixture
    def multi_site_dataset(self) -> TimeSeriesDataset:
        """Create a multi-site, single-pollutant dataset."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=20, freq="h"),
                "site_id": ["S1"] * 10 + ["S2"] * 10,
                "pollutant": ["PM25"] * 20,
                "conc": list(range(1, 11)) + list(range(11, 21)),
                "flag": [QCFlag.VALID.value] * 20,
            }
        )
        return TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

    @pytest.fixture
    def multi_pollutant_dataset(self) -> TimeSeriesDataset:
        """Create a single-site, multi-pollutant dataset."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=20, freq="h"),
                "site_id": ["S1"] * 20,
                "pollutant": ["PM25"] * 10 + ["NO2"] * 10,
                "conc": list(range(1, 11)) + list(range(11, 21)),
                "flag": [QCFlag.VALID.value] * 20,
            }
        )
        return TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

    @pytest.fixture
    def multi_site_multi_pollutant_dataset(self) -> TimeSeriesDataset:
        """Create a multi-site, multi-pollutant dataset."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=40, freq="h"),
                "site_id": ["S1"] * 10 + ["S2"] * 10 + ["S1"] * 10 + ["S2"] * 10,
                "pollutant": ["PM25"] * 20 + ["NO2"] * 20,
                "conc": list(range(1, 41)),
                "flag": [QCFlag.VALID.value] * 40,
            }
        )
        return TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

    def test_group_by_site_creates_separate_groups(self, multi_site_dataset):
        """Test that grouping by site_id creates separate statistics per site."""
        result = compute_descriptives(
            dataset=multi_site_dataset,
            group_by=["site_id"],
            pollutant_col="pollutant",
            conc_col="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have results for both sites
        sites = result["site_id"].unique()
        assert set(sites) == {"S1", "S2"}

        # Each site should have 9 statistics
        for site in ["S1", "S2"]:
            site_rows = result[result["site_id"] == site]
            assert len(site_rows) == 9  # 9 statistics per site

    def test_group_by_site_correct_values(self, multi_site_dataset):
        """Test that grouped statistics compute correctly per site."""
        result = compute_descriptives(
            dataset=multi_site_dataset,
            group_by=["site_id"],
            pollutant_col="pollutant",
            conc_col="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Check S1 statistics (values 1-10)
        s1_rows = result[result["site_id"] == "S1"]
        s1_stats = dict(zip(s1_rows["stat"], s1_rows["value"]))
        assert s1_stats[StatisticType.MEAN.value] == pytest.approx(5.5)
        assert s1_stats[StatisticType.MIN.value] == pytest.approx(1.0)
        assert s1_stats[StatisticType.MAX.value] == pytest.approx(10.0)

        # Check S2 statistics (values 11-20)
        s2_rows = result[result["site_id"] == "S2"]
        s2_stats = dict(zip(s2_rows["stat"], s2_rows["value"]))
        assert s2_stats[StatisticType.MEAN.value] == pytest.approx(15.5)
        assert s2_stats[StatisticType.MIN.value] == pytest.approx(11.0)
        assert s2_stats[StatisticType.MAX.value] == pytest.approx(20.0)

    def test_multi_pollutant_no_grouping(self, multi_pollutant_dataset):
        """Test multiple pollutants without additional grouping."""
        result = compute_descriptives(
            dataset=multi_pollutant_dataset,
            group_by=None,
            pollutant_col="pollutant",
            conc_col="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have results for both pollutants
        pollutants = result["pollutant"].unique()
        assert set(pollutants) == {"PM25", "NO2"}

        # Each pollutant should have 9 statistics
        for pollutant in ["PM25", "NO2"]:
            pollutant_rows = result[result["pollutant"] == pollutant]
            assert len(pollutant_rows) == 9

    def test_multi_pollutant_correct_values(self, multi_pollutant_dataset):
        """Test that multi-pollutant statistics compute correctly."""
        result = compute_descriptives(
            dataset=multi_pollutant_dataset,
            group_by=None,
            pollutant_col="pollutant",
            conc_col="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Check PM25 statistics (values 1-10)
        pm25_rows = result[result["pollutant"] == "PM25"]
        pm25_stats = dict(zip(pm25_rows["stat"], pm25_rows["value"]))
        assert pm25_stats[StatisticType.MEAN.value] == pytest.approx(5.5)

        # Check NO2 statistics (values 11-20)
        no2_rows = result[result["pollutant"] == "NO2"]
        no2_stats = dict(zip(no2_rows["stat"], no2_rows["value"]))
        assert no2_stats[StatisticType.MEAN.value] == pytest.approx(15.5)

    def test_group_by_site_multi_pollutant(self, multi_site_multi_pollutant_dataset):
        """Test grouping by site with multiple pollutants."""
        result = compute_descriptives(
            dataset=multi_site_multi_pollutant_dataset,
            group_by=["site_id"],
            pollutant_col="pollutant",
            conc_col="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have results for 2 sites × 2 pollutants = 4 groups
        # Each group has 9 statistics = 36 total rows
        assert len(result) == 36

        # Check that we have all combinations
        groups = result[["site_id", "pollutant"]].drop_duplicates()
        expected_groups = {
            ("S1", "PM25"),
            ("S1", "NO2"),
            ("S2", "PM25"),
            ("S2", "NO2"),
        }
        actual_groups = set(zip(groups["site_id"], groups["pollutant"]))
        assert actual_groups == expected_groups

    def test_group_by_multiple_columns(self):
        """Test grouping by multiple columns."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=20, freq="h"),
                "site_id": ["S1"] * 10 + ["S2"] * 10,
                "region": ["North"] * 10 + ["South"] * 10,
                "pollutant": ["PM25"] * 20,
                "conc": list(range(1, 21)),
                "flag": [QCFlag.VALID.value] * 20,
            }
        )
        dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

        result = compute_descriptives(
            dataset=dataset,
            group_by=["site_id", "region"],
            pollutant_col="pollutant",
            conc_col="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have both grouping columns in result
        assert "site_id" in result.columns
        assert "region" in result.columns

        # Should have 2 groups (S1/North and S2/South) × 9 stats = 18 rows
        assert len(result) == 18

    def test_group_counts_correct(self, multi_site_dataset):
        """Test that group counts are correct."""
        result = compute_descriptives(
            dataset=multi_site_dataset,
            group_by=["site_id"],
            pollutant_col="pollutant",
            conc_col="conc",
            flag_col="flag",
        )

        # Convert to pandas for easier testing
        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Each site should have n_total=10
        for site in ["S1", "S2"]:
            site_rows = result[result["site_id"] == site]
            assert (site_rows["n_total"] == 10).all()
            assert (site_rows["n_valid"] == 10).all()
            assert (site_rows["n_missing"] == 0).all()

    def test_empty_group_after_filtering(self):
        """Test handling when one group becomes empty after filtering."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=10, freq="h"),
                "site_id": ["S1"] * 5 + ["S2"] * 5,
                "pollutant": ["PM25"] * 10,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "flag": [QCFlag.VALID.value] * 5 + [QCFlag.INVALID.value] * 5,
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

        # Should still have both sites in results
        assert set(result["site_id"].unique()) == {"S1", "S2"}

        # S1 should have valid data
        s1_rows = result[result["site_id"] == "S1"]
        assert (s1_rows["n_valid"] == 5).all()

        # S2 should have all invalid (n_valid=0, values are NaN)
        s2_rows = result[result["site_id"] == "S2"]
        assert (s2_rows["n_valid"] == 0).all()
        assert s2_rows["value"].isna().all()
