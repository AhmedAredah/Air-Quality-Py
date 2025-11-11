"""
Unit tests for trend unit enforcement.

Tests that slope units are correctly computed as conc_unit / time_unit.
"""

from datetime import datetime, timedelta

import polars as pl
import pytest

from air_quality.analysis.trend import compute_linear_trend
from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.exceptions import UnitError
from air_quality.units import TimeUnit


class TestTrendUnits:
    """Test unit enforcement for trend analysis."""

    def test_slope_units_computed_correctly(self) -> None:
        """Test that slope units = conc_unit / time_unit."""
        # Create data with units: ppb for concentration
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i) for i in range(10)]
        concentrations = [2.0 * i + 5.0 for i in range(10)]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["NO2"] * 10,
                "flag": ["valid"] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_polars(
            df=df,
            time_index_name="datetime",
            column_units={"concentration": "ppb"},
        )

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.DAY,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
        )

        row = result.row(0, named=True)

        # Check slope units
        assert "slope_units" in row
        assert row["slope_units"] == "ppb/day"

    def test_different_concentration_units(self) -> None:
        """Test with different concentration units (ug/m3)."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i) for i in range(10)]
        concentrations = [2.0 * i + 5.0 for i in range(10)]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["PM25"] * 10,
                "flag": ["valid"] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_polars(
            df=df,
            time_index_name="datetime",
            column_units={"concentration": "ug/m3"},
        )

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.DAY,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
        )

        row = result.row(0, named=True)

        # Check slope units
        assert row["slope_units"] == "ug/m3/day"

    def test_calendar_year_time_unit_in_slope_units(self) -> None:
        """Test slope units with calendar_year time unit."""
        dates = [
            datetime(2022, 1, 1, 0, 0, 0),
            datetime(2023, 1, 1, 0, 0, 0),
            datetime(2024, 1, 1, 0, 0, 0),
        ]
        concentrations = [100.0, 105.0, 110.0]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["O3"] * 3,
                "flag": ["valid"] * 3,
            }
        )

        dataset = TimeSeriesDataset.from_polars(
            df=df,
            time_index_name="datetime",
            column_units={"concentration": "ppm"},
        )

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.CALENDAR_YEAR,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
        )

        row = result.row(0, named=True)

        # Check slope units
        assert row["slope_units"] == "ppm/calendar_year"

    def test_hour_time_unit_in_slope_units(self) -> None:
        """Test slope units with hour time unit."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(hours=i) for i in range(24)]
        concentrations = [0.5 * i + 2.0 for i in range(24)]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["CO"] * 24,
                "flag": ["valid"] * 24,
            }
        )

        dataset = TimeSeriesDataset.from_polars(
            df=df,
            time_index_name="datetime",
            column_units={"concentration": "ppm"},
        )

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.HOUR,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
        )

        row = result.row(0, named=True)

        # Check slope units
        assert row["slope_units"] == "ppm/hour"

    def test_missing_units_raises_error(self) -> None:
        """Test that missing concentration units raises UnitError."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i) for i in range(10)]
        concentrations = [2.0 * i + 5.0 for i in range(10)]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["NO2"] * 10,
                "flag": ["valid"] * 10,
            }
        )

        # Create dataset WITHOUT concentration units
        dataset = TimeSeriesDataset.from_polars(
            df=df,
            time_index_name="datetime",
            column_units={},  # No units specified
        )

        with pytest.raises(UnitError, match="concentration.*unit"):
            compute_linear_trend(
                dataset=dataset,
                time_unit=TimeUnit.DAY,
                category_col="pollutant",
                datetime_col="datetime",
                value_col="concentration",
                flag_col="flag",
            )

    def test_missing_units_allowed_with_override(self) -> None:
        """Test that missing units are allowed with allow_missing_units=True."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i) for i in range(10)]
        concentrations = [2.0 * i + 5.0 for i in range(10)]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["NO2"] * 10,
                "flag": ["valid"] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_polars(
            df=df,
            time_index_name="datetime",
            column_units={},  # No units
        )

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.DAY,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
            allow_missing_units=True,  # Override
        )

        row = result.row(0, named=True)

        # Slope should still be computed
        assert "slope" in row
        assert row["slope"] is not None

        # Slope units should be None or "unknown"
        assert row.get("slope_units") in [None, "unknown", "unknown/day"]

    def test_units_without_dataset(self) -> None:
        """Test that without dataset, units are not enforced."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i) for i in range(10)]
        concentrations = [2.0 * i + 5.0 for i in range(10)]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["NO2"] * 10,
                "flag": ["valid"] * 10,
            }
        )

        # Call without dataset parameter (create minimal dataset)
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

        # Should compute slope without units
        assert "slope" in row
        assert row["slope"] is not None

    def test_multiple_pollutants_with_units(self) -> None:
        """Test multiple pollutants with unit tracking."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i) for i in range(10)] * 2

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": [2.0 * i + 5.0 for i in range(10)] * 2,
                "pollutant": ["NO2"] * 10 + ["PM25"] * 10,
                "flag": ["valid"] * 20,
            }
        )

        dataset = TimeSeriesDataset.from_polars(
            df=df,
            time_index_name="datetime",
            column_units={"concentration": "ug/m3"},
        )

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.DAY,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
        )

        collected = result

        # Both pollutants should have same slope units
        for row in collected.iter_rows(named=True):
            assert row["slope_units"] == "ug/m3/day"
