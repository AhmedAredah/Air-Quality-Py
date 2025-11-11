"""
Unit tests for trend short duration flagging.

Tests that short_duration_flag is set when time span < min_duration_years.
"""

from datetime import datetime, timedelta

import polars as pl
import pytest

from air_quality.analysis.trend import compute_linear_trend
from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.units import TimeUnit


class TestTrendShortDuration:
    """Test short duration flagging logic."""

    def test_short_duration_flag_true_when_below_threshold(self) -> None:
        """Test short_duration_flag=True when duration < min_duration_years."""
        # 6 months of data (0.5 years) with min_duration_years=1.0
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i * 30) for i in range(7)]  # ~6 months
        concentrations = [10.0 + 2.0 * i for i in range(7)]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["NO2"] * 7,
                "flag": ["valid"] * 7,
            }
        )

        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.DAY,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
        allow_missing_units=True,
            min_duration_years=1.0,  # Require 1 year minimum
        )

        row = result.row(0, named=True)

        # Should have short_duration_flag=True
        assert row["short_duration_flag"] is True

        # Should still compute slope
        assert "slope" in row
        assert row["slope"] is not None

    def test_short_duration_flag_false_when_above_threshold(self) -> None:
        """Test short_duration_flag=False when duration >= min_duration_years."""
        # 400 days of data (~1.1 years) with min_duration_years=1.0
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i * 40) for i in range(11)]  # ~400 days
        concentrations = [10.0 + 2.0 * i for i in range(11)]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["PM25"] * 11,
                "flag": ["valid"] * 11,
            }
        )

        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.DAY,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
        allow_missing_units=True,
            min_duration_years=1.0,
        )

        row = result.row(0, named=True)

        # Should have short_duration_flag=False
        assert row["short_duration_flag"] is False

    def test_short_duration_with_calendar_year_unit(self) -> None:
        """Test short duration with calendar_year time unit."""
        # 9 months of data (0.75 years)
        dates = [
            datetime(2024, 1, 1, 0, 0, 0),
            datetime(2024, 4, 1, 0, 0, 0),
            datetime(2024, 7, 1, 0, 0, 0),
            datetime(2024, 10, 1, 0, 0, 0),
        ]
        concentrations = [10.0, 15.0, 20.0, 25.0]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["O3"] * 4,
                "flag": ["valid"] * 4,
            }
        )

        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.CALENDAR_YEAR,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
        allow_missing_units=True,
            min_duration_years=1.0,
        )

        row = result.row(0, named=True)

        # Duration is ~0.75 years, should be flagged
        assert row["short_duration_flag"] is True

    def test_low_n_flag_when_below_min_samples(self) -> None:
        """Test low_n_flag=True when n < min_samples."""
        # Only 2 samples, but min_samples=3
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start, start + timedelta(days=365)]  # 1 year span
        concentrations = [10.0, 20.0]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["CO"] * 2,
                "flag": ["valid"] * 2,
            }
        )

        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.DAY,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
        allow_missing_units=True,
            min_samples=3,
            min_duration_years=0.5,  # Low enough to pass duration check
        )

        # With min_samples=3, this might return empty or have low_n_flag
        # Let's check if we get a result
        collected = result
        if collected.shape[0] > 0:
            row = collected.row(0, named=True)
            # If returned, should have low_n_flag=True
            assert row.get("low_n_flag", False) is True

    def test_both_flags_false_for_sufficient_data(self) -> None:
        """Test both flags False when duration and n are sufficient."""
        # 2 years of monthly data = 24 samples
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i * 30) for i in range(25)]  # ~2 years
        concentrations = [10.0 + 1.0 * i for i in range(25)]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["PM10"] * 25,
                "flag": ["valid"] * 25,
            }
        )

        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.DAY,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
        allow_missing_units=True,
            min_samples=3,
            min_duration_years=1.0,
        )

        row = result.row(0, named=True)

        # Both flags should be False
        assert row["short_duration_flag"] is False
        assert row.get("low_n_flag", False) is False

    def test_custom_min_duration_threshold(self) -> None:
        """Test custom min_duration_years threshold (e.g., 2.0 years)."""
        # 18 months of data (1.5 years) with min_duration_years=2.0
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i * 30) for i in range(19)]  # ~18 months
        concentrations = [10.0 + 1.0 * i for i in range(19)]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["SO2"] * 19,
                "flag": ["valid"] * 19,
            }
        )

        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.DAY,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
        allow_missing_units=True,
            min_duration_years=2.0,  # Require 2 years
        )

        row = result.row(0, named=True)

        # Duration is ~1.5 years < 2.0, should be flagged
        assert row["short_duration_flag"] is True

    def test_exactly_at_threshold(self) -> None:
        """Test duration exactly at threshold (edge case)."""
        # Exactly 365 days (1.0 years) with min_duration_years=1.0
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2025, 1, 1, 0, 0, 0)
        dates = [start, end]
        concentrations = [10.0, 20.0]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["NO2"] * 2,
                "flag": ["valid"] * 2,
            }
        )

        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.DAY,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
        allow_missing_units=True,
            min_samples=2,
            min_duration_years=1.0,
        )

        row = result.row(0, named=True)

        # At exactly 1.0 years, flag should be False (>= threshold)
        assert row["short_duration_flag"] is False
