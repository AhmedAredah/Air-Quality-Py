"""
Unit tests for basic trend analysis with day time unit.

Tests linear slope computation for simple, known linear data.
"""

from datetime import datetime, timedelta

import polars as pl
import pytest

from air_quality.analysis.trend import compute_linear_trend
from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.units import TimeUnit


class TestLinearTrendBasic:
    """Test basic linear trend computation with day time unit."""

    def test_perfect_linear_trend_day_unit(self) -> None:
        """Test perfect linear trend: y = 2*x + 5 with day time unit."""
        # Create 10 days of perfect linear data: y = 2*x + 5
        # where x is days from start
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i) for i in range(10)]
        concentrations = [2.0 * i + 5.0 for i in range(10)]  # slope=2, intercept=5

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["NO2"] * 10,
                "flag": ["valid"] * 10,  # Use string flags
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
        )

        # Should have one trend result for NO2
        collected = result
        assert collected.shape[0] == 1
        row = collected.row(0, named=True)

        # Check slope (should be 2.0 concentration units per day)
        assert abs(row["slope"] - 2.0) < 1e-6

        # Check intercept (should be 5.0)
        assert abs(row["intercept"] - 5.0) < 1e-6

        # Check R² (should be 1.0 for perfect linear)
        assert abs(row["r_squared"] - 1.0) < 1e-6

        # Check sample count
        assert row["n"] == 10

    def test_negative_slope_day_unit(self) -> None:
        """Test negative slope: y = -0.5*x + 10."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i) for i in range(20)]
        concentrations = [-0.5 * i + 10.0 for i in range(20)]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["O3"] * 20,
                "flag": ["valid"] * 20,
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
        )

        row = result.row(0, named=True)

        # Negative slope
        assert abs(row["slope"] - (-0.5)) < 1e-6

        # Intercept
        assert abs(row["intercept"] - 10.0) < 1e-6

        # R²
        assert abs(row["r_squared"] - 1.0) < 1e-6

    def test_zero_slope_constant_concentration(self) -> None:
        """Test zero slope when concentration is constant."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i) for i in range(15)]
        concentrations = [42.0] * 15  # Constant

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["PM25"] * 15,
                "flag": ["valid"] * 15,
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
        )

        row = result.row(0, named=True)

        # Slope should be ~0
        assert abs(row["slope"]) < 1e-6

        # Intercept should be ~42
        assert abs(row["intercept"] - 42.0) < 1e-6

        # R² undefined for constant y, should handle gracefully (NaN or 0)
        # Accept either NaN or 0.0
        r_sq = row["r_squared"]
        assert (
            r_sq is None
            or abs(r_sq) < 1e-6
            or (isinstance(r_sq, float) and r_sq != r_sq)
        )

    def test_with_qc_filtering(self) -> None:
        """Test that QC flags filter out bad data."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i) for i in range(10)]
        concentrations = [2.0 * i + 5.0 for i in range(10)]
        flags = ["valid"] * 10

        # Mark some data as bad
        flags[3] = "invalid"
        flags[7] = "outlier"
        concentrations[3] = 999.0  # Outlier that should be filtered
        concentrations[7] = -999.0

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["NO2"] * 10,
                "flag": flags,
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
        )

        row = result.row(0, named=True)

        # Should still have slope ~2 after filtering
        assert abs(row["slope"] - 2.0) < 0.1

        # Sample count should be 8 (2 filtered out)
        assert row["n"] == 8

    def test_multiple_pollutants(self) -> None:
        """Test computing trends for multiple pollutants."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i) for i in range(10)] * 3  # 3 pollutants

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": (
                    [2.0 * i + 5.0 for i in range(10)]
                    + [
                        -0.5 * i + 10.0 for i in range(10)
                    ]  # NO2: slope=2  # O3: slope=-0.5
                    + [1.0 * i + 0.0 for i in range(10)]  # PM25: slope=1
                ),
                "pollutant": ["NO2"] * 10 + ["O3"] * 10 + ["PM25"] * 10,
                "flag": ["valid"] * 30,
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
        )

        collected = result
        assert collected.shape[0] == 3

        # Check each pollutant
        slopes = {
            row["pollutant"]: row["slope"] for row in collected.iter_rows(named=True)
        }
        assert abs(slopes["NO2"] - 2.0) < 1e-6
        assert abs(slopes["O3"] - (-0.5)) < 1e-6
        assert abs(slopes["PM25"] - 1.0) < 1e-6

    def test_insufficient_samples_returns_none(self) -> None:
        """Test that insufficient samples (n < min_samples) returns None or empty."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i) for i in range(2)]  # Only 2 samples
        concentrations = [5.0, 10.0]

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
            min_samples=3,  # Require at least 3 samples
        )

        # Should return empty result
        assert result.shape[0] == 0

    def test_hour_time_unit(self) -> None:
        """Test with hour time unit."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(hours=i) for i in range(24)]
        concentrations = [0.5 * i + 2.0 for i in range(24)]  # slope=0.5 per hour

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["CO"] * 24,
                "flag": ["valid"] * 24,
            }
        )

        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.HOUR,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
        allow_missing_units=True,
        )

        row = result.row(0, named=True)

        # Slope should be 0.5 per hour
        assert abs(row["slope"] - 0.5) < 1e-6

        # Intercept should be 2.0
        assert abs(row["intercept"] - 2.0) < 1e-6
