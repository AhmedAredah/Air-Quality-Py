"""Tests for selective statistics computation with stats parameter."""

import polars as pl
import pytest

from air_quality.analysis.descriptive import (
    compute_descriptives,
    DescriptiveStatsOperation,
)
from air_quality.dataset.time_series import TimeSeriesDataset


class TestSelectiveStats:
    """Test computing only requested statistics."""

    def test_compute_only_mean(self) -> None:
        """Test computing only mean statistic."""
        df = pl.DataFrame({
            "datetime": ["2024-01-01"] * 10,
            "pollutant": ["PM25"] * 10,
            "conc": [float(i) for i in range(10)],
            "flag": ["valid"] * 10,
        })
        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        result = compute_descriptives(
            dataset=dataset,
            value_cols="conc",
            stats=[DescriptiveStatsOperation.MEAN],
        )

        # Should only have mean statistic (plus count columns)
        stats = result.select("stat").unique().to_series().to_list()
        assert "mean" in stats
        assert "median" not in stats
        assert "std" not in stats
        assert "min" not in stats
        assert "max" not in stats

    def test_compute_mean_and_std(self) -> None:
        """Test computing only mean and std."""
        df = pl.DataFrame({
            "datetime": ["2024-01-01"] * 10,
            "pollutant": ["PM25"] * 10,
            "conc": [float(i) for i in range(10)],
            "flag": ["valid"] * 10,
        })
        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        result = compute_descriptives(
            dataset=dataset,
            value_cols="conc",
            stats=[DescriptiveStatsOperation.MEAN, DescriptiveStatsOperation.STD],
        )

        # Should only have mean and std
        stats = result.select("stat").unique().to_series().to_list()
        assert "mean" in stats
        assert "std" in stats
        assert "median" not in stats
        assert "min" not in stats
        assert "max" not in stats

    def test_compute_all_stats_when_none(self) -> None:
        """Test that stats=None computes all statistics."""
        df = pl.DataFrame({
            "datetime": ["2024-01-01"] * 10,
            "pollutant": ["PM25"] * 10,
            "conc": [float(i) for i in range(10)],
            "flag": ["valid"] * 10,
        })
        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        result = compute_descriptives(
            dataset=dataset,
            value_cols="conc",
            stats=None,  # Default: all stats
        )

        # Should have all basic stats
        stats = result.select("stat").unique().to_series().to_list()
        assert "mean" in stats
        assert "median" in stats
        assert "std" in stats
        assert "min" in stats
        assert "max" in stats
        # Should also have default quantiles
        assert "q05" in stats or "q25" in stats  # At least one quantile

    def test_compute_min_max_only(self) -> None:
        """Test computing only min and max."""
        df = pl.DataFrame({
            "datetime": ["2024-01-01"] * 10,
            "pollutant": ["PM25"] * 10,
            "conc": [float(i) for i in range(10)],
            "flag": ["valid"] * 10,
        })
        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        result = compute_descriptives(
            dataset=dataset,
            value_cols="conc",
            stats=[DescriptiveStatsOperation.MIN, DescriptiveStatsOperation.MAX],
        )

        stats = result.select("stat").unique().to_series().to_list()
        assert "min" in stats
        assert "max" in stats
        assert "mean" not in stats
        assert "median" not in stats
        assert "std" not in stats

    def test_quantiles_only_when_requested(self) -> None:
        """Test that quantiles are only computed when requested."""
        df = pl.DataFrame({
            "datetime": ["2024-01-01"] * 10,
            "pollutant": ["PM25"] * 10,
            "conc": [float(i) for i in range(10)],
            "flag": ["valid"] * 10,
        })
        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        # Without quantiles
        result_no_q = compute_descriptives(
            dataset=dataset,
            value_cols="conc",
            stats=[DescriptiveStatsOperation.MEAN, DescriptiveStatsOperation.STD],
        )
        stats_no_q = result_no_q.select("stat").unique().to_series().to_list()
        assert not any(s.startswith("q") for s in stats_no_q if s not in ["mean", "std"])

        # With quantiles
        result_with_q = compute_descriptives(
            dataset=dataset,
            value_cols="conc",
            stats=[DescriptiveStatsOperation.MEAN, DescriptiveStatsOperation.QUANTILES],
        )
        stats_with_q = result_with_q.select("stat").unique().to_series().to_list()
        assert "mean" in stats_with_q
        assert any(s.startswith("q") for s in stats_with_q)
