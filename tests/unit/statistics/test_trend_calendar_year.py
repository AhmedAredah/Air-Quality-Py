"""
Unit tests for trend analysis with calendar year time unit.

Tests fractional year computation using calendar-aware logic.
"""

from datetime import datetime

import polars as pl
import pytest

from air_quality.analysis.trend import compute_linear_trend
from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.units import TimeUnit


class TestLinearTrendCalendarYear:
    """Test trend computation with calendar_year time unit."""

    def test_one_year_span_calendar_year(self) -> None:
        """Test trend over exactly one calendar year."""
        # Jan 1, 2024 to Jan 1, 2025 = 1.0 calendar years
        dates = [
            datetime(2024, 1, 1, 0, 0, 0),
            datetime(2024, 4, 1, 0, 0, 0),
            datetime(2024, 7, 1, 0, 0, 0),
            datetime(2024, 10, 1, 0, 0, 0),
            datetime(2025, 1, 1, 0, 0, 0),
        ]
        # Linear trend: concentration increases by 10 units per year
        # At t=0 (2024-01-01): conc=10
        # At t=1.0 (2025-01-01): conc=20
        concentrations = [10.0, 12.5, 15.0, 17.5, 20.0]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["NO2"] * 5,
                "flag": ["valid"] * 5,
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
        )

        row = result.row(0, named=True)

        # Slope should be ~10 units per calendar year
        assert abs(row["slope"] - 10.0) < 0.5

        # Check duration is computed
        assert "duration_years" in row or "time_span" in row

    def test_multi_year_span_calendar_year(self) -> None:
        """Test trend over multiple calendar years (3 years)."""
        # 2022-01-01 to 2025-01-01 = 3.0 calendar years
        dates = [
            datetime(2022, 1, 1, 0, 0, 0),
            datetime(2023, 1, 1, 0, 0, 0),
            datetime(2024, 1, 1, 0, 0, 0),
            datetime(2025, 1, 1, 0, 0, 0),
        ]
        # Linear: slope = 5 units/year, intercept = 100
        concentrations = [100.0, 105.0, 110.0, 115.0]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["PM25"] * 4,
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
        )

        row = result.row(0, named=True)

        # Slope should be ~5 units per calendar year
        assert abs(row["slope"] - 5.0) < 0.5

    def test_fractional_year_mid_year_span(self) -> None:
        """Test fractional year computation for mid-year span."""
        # 2024-01-01 to 2024-07-01 = ~0.5 calendar years (6 months)
        dates = [
            datetime(2024, 1, 1, 0, 0, 0),
            datetime(2024, 2, 1, 0, 0, 0),
            datetime(2024, 3, 1, 0, 0, 0),
            datetime(2024, 4, 1, 0, 0, 0),
            datetime(2024, 5, 1, 0, 0, 0),
            datetime(2024, 6, 1, 0, 0, 0),
            datetime(2024, 7, 1, 0, 0, 0),
        ]
        # If slope is 20 units/year, then over 6 months (0.5 years) we expect +10 units
        concentrations = [
            50.0,
            50.0 + 20.0 / 12,  # 1 month
            50.0 + 2 * 20.0 / 12,  # 2 months
            50.0 + 3 * 20.0 / 12,  # 3 months
            50.0 + 4 * 20.0 / 12,  # 4 months
            50.0 + 5 * 20.0 / 12,  # 5 months
            50.0 + 6 * 20.0 / 12,  # 6 months
        ]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["O3"] * 7,
                "flag": ["valid"] * 7,
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
        )

        row = result.row(0, named=True)

        # Slope should be ~20 units per calendar year
        assert abs(row["slope"] - 20.0) < 1.0

    def test_leap_year_handling(self) -> None:
        """Test that leap year is handled correctly (366 days in 2024)."""
        # 2024 is a leap year
        # Span from 2024-01-01 to 2024-12-31 should be ~1.0 calendar years
        dates = [
            datetime(2024, 1, 1, 0, 0, 0),
            datetime(2024, 3, 1, 0, 0, 0),
            datetime(2024, 6, 1, 0, 0, 0),
            datetime(2024, 9, 1, 0, 0, 0),
            datetime(2024, 12, 31, 0, 0, 0),
        ]
        concentrations = [10.0, 15.0, 20.0, 25.0, 30.0]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["NO2"] * 5,
                "flag": ["valid"] * 5,
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
        )

        row = result.row(0, named=True)

        # Slope should be ~20 units per calendar year (30-10=20 over ~1 year)
        assert abs(row["slope"] - 20.0) < 2.0

    def test_calendar_month_time_unit(self) -> None:
        """Test with calendar_month time unit."""
        # Monthly data over 12 months
        dates = [datetime(2024, month, 1, 0, 0, 0) for month in range(1, 13)]
        # Slope = 2 units per month
        concentrations = [10.0 + 2.0 * i for i in range(12)]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["PM10"] * 12,
                "flag": ["valid"] * 12,
            }
        )

        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.CALENDAR_MONTH,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
        allow_missing_units=True,
        )

        row = result.row(0, named=True)

        # Slope should be ~2 units per calendar month
        assert abs(row["slope"] - 2.0) < 0.5

    def test_cross_year_boundary(self) -> None:
        """Test trend spanning across year boundary (Dec to Jan)."""
        # December 2023 to February 2024
        dates = [
            datetime(2023, 12, 1, 0, 0, 0),
            datetime(2023, 12, 15, 0, 0, 0),
            datetime(2024, 1, 1, 0, 0, 0),
            datetime(2024, 1, 15, 0, 0, 0),
            datetime(2024, 2, 1, 0, 0, 0),
        ]
        # Slope = 12 units per month = 144 units per year
        # Over ~2 months = ~24 units total increase
        concentrations = [100.0, 106.0, 112.0, 118.0, 124.0]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["CO"] * 5,
                "flag": ["valid"] * 5,
            }
        )

        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.CALENDAR_MONTH,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
        allow_missing_units=True,
        )

        row = result.row(0, named=True)

        # Slope should be ~12 units per calendar month
        assert abs(row["slope"] - 12.0) < 2.0
