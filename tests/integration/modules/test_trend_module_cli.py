"""
Integration tests for TrendModule CLI and dashboard reports.

Tests the complete module with CLI and dashboard output.
"""

from datetime import datetime, timedelta

import polars as pl
import pytest

from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.modules.statistics.trend import TrendModule, TrendConfig
from air_quality.units import TimeUnit


class TestTrendModuleCLI:
    """Integration tests for TrendModule CLI and dashboard reports."""

    def test_basic_cli_report(self) -> None:
        """Test basic CLI report generation."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i * 30) for i in range(25)]  # ~2 years
        concentrations = [10.0 + 1.0 * i for i in range(25)]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["NO2"] * 25,
                "flag": ["valid"] * 25,
            }
        )

        dataset = TimeSeriesDataset.from_polars(
            df=df,
            time_index_name="datetime",
            column_units={"concentration": "ppb"},
        )

        config = {
            TrendConfig.TIME_UNIT: "day",
            TrendConfig.CATEGORY_COL: "pollutant",
            TrendConfig.DATETIME_COL: "datetime",
            TrendConfig.VALUE_COL: "concentration",
            TrendConfig.FLAG_COL: "flag",
        }

        module = TrendModule(dataset=dataset, config=config)
        result = module.run()

        # Check CLI report exists
        cli_report = result.report_cli()
        assert cli_report is not None
        assert len(cli_report) > 0

        # Should contain key info
        assert "Trend Analysis" in cli_report or "slope" in cli_report.lower()
        assert "NO2" in cli_report

    def test_dashboard_report_structure(self) -> None:
        """Test dashboard JSON structure."""
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

        config = {
            TrendConfig.TIME_UNIT: "day",
            TrendConfig.CATEGORY_COL: "pollutant",
            TrendConfig.DATETIME_COL: "datetime",
            TrendConfig.VALUE_COL: "concentration",
            TrendConfig.FLAG_COL: "flag",
        }

        module = TrendModule(dataset=dataset, config=config)
        result = module.run()

        # Check dashboard structure
        dashboard_payload = result.report_dashboard()

        dashboard = dashboard_payload["metrics"]
        assert "trends" in dashboard
        assert "time_unit" in dashboard
        assert "config" in dashboard

        # Check trend data
        trends = dashboard["trends"]
        assert len(trends) == 1
        trend = trends[0]
        assert "slope" in trend
        assert "intercept" in trend
        assert "r_squared" in trend
        assert "n" in trend
        assert "pollutant" in trend

    def test_short_duration_flag_in_reports(self) -> None:
        """Test that short_duration_flag appears in reports."""
        # 6 months of data
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i * 30) for i in range(7)]
        concentrations = [10.0 + 2.0 * i for i in range(7)]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["O3"] * 7,
                "flag": ["valid"] * 7,
            }
        )

        dataset = TimeSeriesDataset.from_polars(
            df=df,
            time_index_name="datetime",
            column_units={"concentration": "ppm"},
        )

        config = {
            TrendConfig.TIME_UNIT: "day",
            TrendConfig.MIN_DURATION_YEARS: 1.0,
            TrendConfig.CATEGORY_COL: "pollutant",
            TrendConfig.DATETIME_COL: "datetime",
            TrendConfig.VALUE_COL: "concentration",
            TrendConfig.FLAG_COL: "flag",
        }

        module = TrendModule(dataset=dataset, config=config)
        result = module.run()

        # Check dashboard
        dashboard_payload = result.report_dashboard()

        dashboard = dashboard_payload["metrics"]
        trend = dashboard["trends"][0]
        assert trend["short_duration_flag"] is True

        # Check CLI report
        cli_report = result.report_cli()
        assert "SHORT_DURATION" in cli_report or "short duration" in cli_report.lower()

    def test_grouped_trends(self) -> None:
        """Test grouped trends by location."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i) for i in range(10)] * 2

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": [2.0 * i + 5.0 for i in range(10)] * 2,
                "pollutant": ["NO2"] * 10 + ["PM25"] * 10,
                "location": ["Site A"] * 20,
                "flag": ["valid"] * 20,
            }
        )

        dataset = TimeSeriesDataset.from_polars(
            df=df,
            time_index_name="datetime",
            column_units={"concentration": "ug/m3"},
        )

        config = {
            TrendConfig.TIME_UNIT: "day",
            TrendConfig.GROUP_BY: ["pollutant"],
            TrendConfig.CATEGORY_COL: "pollutant",
            TrendConfig.DATETIME_COL: "datetime",
            TrendConfig.VALUE_COL: "concentration",
            TrendConfig.FLAG_COL: "flag",
        }

        module = TrendModule(dataset=dataset, config=config)
        result = module.run()

        # Should have 2 trends (NO2 and PM25)
        dashboard_payload = result.report_dashboard()

        dashboard = dashboard_payload["metrics"]
        assert len(dashboard["trends"]) == 2

        # Check CLI shows both
        cli_report = result.report_cli()
        assert "NO2" in cli_report
        assert "PM25" in cli_report

    def test_calendar_year_in_reports(self) -> None:
        """Test calendar_year time unit in reports."""
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
                "pollutant": ["CO"] * 3,
                "flag": ["valid"] * 3,
            }
        )

        dataset = TimeSeriesDataset.from_polars(
            df=df,
            time_index_name="datetime",
            column_units={"concentration": "ppm"},
        )

        config = {
            TrendConfig.TIME_UNIT: "calendar_year",
            TrendConfig.CATEGORY_COL: "pollutant",
            TrendConfig.DATETIME_COL: "datetime",
            TrendConfig.VALUE_COL: "concentration",
            TrendConfig.FLAG_COL: "flag",
        }

        module = TrendModule(dataset=dataset, config=config)
        result = module.run()

        # Check dashboard shows calendar_year
        dashboard_payload = result.report_dashboard()

        dashboard = dashboard_payload["metrics"]
        assert dashboard["time_unit"] == "calendar_year"

        # Check slope units
        trend = dashboard["trends"][0]
        assert "calendar_year" in trend["slope_units"]

        # Check CLI shows calendar_year
        cli_report = result.report_cli()
        assert "calendar_year" in cli_report.lower()

    def test_time_bounds_in_dashboard(self) -> None:
        """Test that time bounds are included in dashboard."""
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

        dataset = TimeSeriesDataset.from_polars(
            df=df,
            time_index_name="datetime",
            column_units={"concentration": "ppb"},
        )

        config = {
            TrendConfig.TIME_UNIT: "day",
            TrendConfig.MIN_SAMPLES: 2,
            TrendConfig.CATEGORY_COL: "pollutant",
            TrendConfig.DATETIME_COL: "datetime",
            TrendConfig.VALUE_COL: "concentration",
            TrendConfig.FLAG_COL: "flag",
        }

        module = TrendModule(dataset=dataset, config=config)
        result = module.run()

        # Check dashboard has time bounds
        dashboard_payload = result.report_dashboard()

        dashboard = dashboard_payload["metrics"]
        assert "time_bounds" in dashboard or "start_time" in dashboard["trends"][0]

    def test_provenance_in_dashboard(self) -> None:
        """Test that provenance metadata is included."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i) for i in range(10)]
        concentrations = [2.0 * i + 5.0 for i in range(10)]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["PM10"] * 10,
                "flag": ["valid"] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_polars(
            df=df,
            time_index_name="datetime",
            column_units={"concentration": "ug/m3"},
        )

        config = {
            TrendConfig.TIME_UNIT: "day",
            TrendConfig.CATEGORY_COL: "pollutant",
            TrendConfig.DATETIME_COL: "datetime",
            TrendConfig.VALUE_COL: "concentration",
            TrendConfig.FLAG_COL: "flag",
        }

        module = TrendModule(dataset=dataset, config=config)
        result = module.run()

        # Check provenance exists in dashboard payload (top-level, not in metrics)
        dashboard_payload = result.report_dashboard()

        assert "provenance" in dashboard_payload
        assert dashboard_payload["provenance"] is not None

    def test_units_warning_in_cli_when_missing(self) -> None:
        """Test that CLI shows WARNING when units are missing."""
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

        # No units specified
        dataset = TimeSeriesDataset.from_polars(
            df=df,
            time_index_name="datetime",
            column_units={},
        )

        config = {
            TrendConfig.TIME_UNIT: "day",
            TrendConfig.CATEGORY_COL: "pollutant",
            TrendConfig.DATETIME_COL: "datetime",
            TrendConfig.VALUE_COL: "concentration",
            TrendConfig.FLAG_COL: "flag",
            TrendConfig.ALLOW_MISSING_UNITS: True,  # Allow units to be missing
        }

        module = TrendModule(dataset=dataset, config=config)

        # Run with allow_missing_units override
        result = module.run()
        cli_report = result.report_cli()
        # Should show unknown units in slope_units
        assert "unknown" in cli_report.lower() or "slope_units" in cli_report.lower()

    def test_empty_result_when_all_filtered(self) -> None:
        """Test that empty result is handled when all data filtered by QC."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        dates = [start + timedelta(days=i) for i in range(10)]
        concentrations = [2.0 * i + 5.0 for i in range(10)]
        flags = ["invalid"] * 10  # All bad

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["NO2"] * 10,
                "flag": flags,
            }
        )

        dataset = TimeSeriesDataset.from_polars(
            df=df,
            time_index_name="datetime",
            column_units={"concentration": "ppb"},
        )

        config = {
            TrendConfig.TIME_UNIT: "day",
            TrendConfig.CATEGORY_COL: "pollutant",
            TrendConfig.DATETIME_COL: "datetime",
            TrendConfig.VALUE_COL: "concentration",
            TrendConfig.FLAG_COL: "flag",
        }

        module = TrendModule(dataset=dataset, config=config)
        result = module.run()

        # Dashboard should show no trends
        dashboard_payload = result.report_dashboard()

        dashboard = dashboard_payload["metrics"]
        assert len(dashboard["trends"]) == 0

        # CLI should indicate no results (check for "Number of trends computed: 0")
        cli_report = result.report_cli()
        assert (
            "Number of trends computed: 0" in cli_report
            or "no trends" in cli_report.lower()
        )
