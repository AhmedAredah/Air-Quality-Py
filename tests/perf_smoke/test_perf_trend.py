"""Performance smoke tests for trend analysis.

Tests that trend computation completes within reasonable time for large datasets.
Target: 100k rows in <2 seconds.
"""

from datetime import datetime, timedelta

import polars as pl
import pytest

from air_quality.analysis.trend import compute_linear_trend
from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.modules.statistics.trend import TrendModule, TrendConfig
from air_quality.units import TimeUnit


class TestTrendPerformance:
    """Performance smoke tests for trend analysis."""

    def test_primitive_performance_100k_rows(self) -> None:
        """Test compute_linear_trend with 100k rows completes in <2s."""
        import time

        # Generate 100k rows of hourly data (~11 years)
        start = datetime(2010, 1, 1, 0, 0, 0)
        n_rows = 100_000
        dates = [start + timedelta(hours=i) for i in range(n_rows)]

        # Create linear trend data with some noise
        import random

        random.seed(42)
        concentrations = [
            10.0 + 0.001 * i + random.gauss(0, 0.5) for i in range(n_rows)
        ]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["PM25"] * n_rows,
                "flag": ["valid"] * n_rows,
            }
        )

        start_time = time.time()

        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.DAY,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
            min_samples=100,
            min_duration_years=1.0,
            allow_missing_units=True,
        )

        # Trigger computation
        collected = result

        elapsed = time.time() - start_time

        # Should complete in <2 seconds
        assert elapsed < 2.0, f"Trend computation took {elapsed:.2f}s (target: <2s)"

        # Verify result
        assert len(collected) == 1
        row = collected.row(0, named=True)
        assert "slope" in row
        assert row["slope"] > 0  # Should detect positive trend

    def test_primitive_performance_multiple_pollutants(self) -> None:
        """Test compute_linear_trend with 100k rows and 4 pollutants."""
        import time

        # Generate 25k rows per pollutant (100k total)
        start = datetime(2010, 1, 1, 0, 0, 0)
        n_per_pollutant = 25_000
        pollutants = ["PM25", "PM10", "NO2", "O3"]

        data_list = []
        for pollutant in pollutants:
            dates = [start + timedelta(hours=i) for i in range(n_per_pollutant)]
            import random

            random.seed(42)
            concentrations = [
                10.0 + 0.001 * i + random.gauss(0, 0.5) for i in range(n_per_pollutant)
            ]

            data_list.append(
                pl.DataFrame(
                    {
                        "datetime": dates,
                        "concentration": concentrations,
                        "pollutant": [pollutant] * n_per_pollutant,
                        "flag": ["valid"] * n_per_pollutant,
                    }
                )
            )

        df = pl.concat(data_list)

        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        start_time = time.time()

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.DAY,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
            min_samples=100,
            min_duration_years=1.0,
            allow_missing_units=True,
        )

        collected = result
        elapsed = time.time() - start_time

        # Should complete in <2 seconds even with grouping
        assert elapsed < 2.0, f"Multi-pollutant trend took {elapsed:.2f}s (target: <2s)"

        # Should have 4 trends (one per pollutant)
        assert len(collected) == 4

    def test_primitive_performance_grouped(self) -> None:
        """Test compute_linear_trend with grouping by site (100k rows, 4 sites)."""
        import time

        # Generate 25k rows per site (100k total)
        start = datetime(2010, 1, 1, 0, 0, 0)
        n_per_site = 25_000
        sites = ["site1", "site2", "site3", "site4"]

        data_list = []
        for site in sites:
            dates = [start + timedelta(hours=i) for i in range(n_per_site)]
            import random

            random.seed(42)
            concentrations = [
                10.0 + 0.001 * i + random.gauss(0, 0.5) for i in range(n_per_site)
            ]

            data_list.append(
                pl.DataFrame(
                    {
                        "datetime": dates,
                        "concentration": concentrations,
                        "pollutant": ["PM25"] * n_per_site,
                        "site_id": [site] * n_per_site,
                        "flag": ["valid"] * n_per_site,
                    }
                )
            )

        df = pl.concat(data_list)

        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        start_time = time.time()

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.DAY,
            group_by=["site_id"],
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
            min_samples=100,
            min_duration_years=1.0,
            allow_missing_units=True,
        )

        collected = result
        elapsed = time.time() - start_time

        # Should complete in <2 seconds with grouping
        assert elapsed < 2.0, f"Grouped trend took {elapsed:.2f}s (target: <2s)"

        # Should have 4 trends (one per site)
        assert len(collected) == 4

    def test_module_end_to_end_performance(self) -> None:
        """Test TrendModule with 50k rows completes efficiently."""
        import time

        # Generate 50k rows for module test (lighter for integration)
        start = datetime(2010, 1, 1, 0, 0, 0)
        n_rows = 50_000
        dates = [start + timedelta(hours=i) for i in range(n_rows)]

        import random

        random.seed(42)
        concentrations = [
            10.0 + 0.001 * i + random.gauss(0, 0.5) for i in range(n_rows)
        ]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["PM25"] * n_rows,
                "flag": ["valid"] * n_rows,
            }
        )

        dataset = TimeSeriesDataset.from_polars(
            df=df,
            time_index_name="datetime",
            column_units={"concentration": "ug/m3"},
        )

        config = {
            TrendConfig.TIME_UNIT: TimeUnit.DAY,
            TrendConfig.CATEGORY_COL: "pollutant",
            TrendConfig.DATETIME_COL: "datetime",
            TrendConfig.VALUE_COL: "concentration",
            TrendConfig.FLAG_COL: "flag",
            TrendConfig.MIN_SAMPLES: 100,
            TrendConfig.MIN_DURATION_YEARS: 1.0,
        }

        module = TrendModule(dataset=dataset, config=config)

        start_time = time.time()
        module.run()
        elapsed = time.time() - start_time

        # Module should complete in <2 seconds
        assert elapsed < 2.0, f"Module execution took {elapsed:.2f}s (target: <2s)"

        # Verify reports can be generated
        cli_report = module.report_cli()
        assert len(cli_report) > 0

        dashboard = module.report_dashboard()
        assert "metrics" in dashboard
        assert "provenance" in dashboard

    def test_calendar_year_performance(self) -> None:
        """Test calendar_year time unit with multi-year data."""
        import time

        # Generate 10 years of monthly data (120 points)
        start = datetime(2010, 1, 1, 0, 0, 0)
        n_months = 120
        dates = [datetime(2010 + i // 12, 1 + (i % 12), 1) for i in range(n_months)]

        import random

        random.seed(42)
        concentrations = [
            10.0 + 0.05 * i + random.gauss(0, 1.0) for i in range(n_months)
        ]

        df = pl.DataFrame(
            {
                "datetime": dates,
                "concentration": concentrations,
                "pollutant": ["PM25"] * n_months,
                "flag": ["valid"] * n_months,
            }
        )

        dataset = TimeSeriesDataset.from_polars(df, time_index_name="datetime")

        start_time = time.time()

        result = compute_linear_trend(
            dataset=dataset,
            time_unit=TimeUnit.CALENDAR_YEAR,
            category_col="pollutant",
            datetime_col="datetime",
            value_col="concentration",
            flag_col="flag",
            min_samples=12,
            min_duration_years=5.0,
            allow_missing_units=True,
        )

        collected = result
        elapsed = time.time() - start_time

        # Should be very fast for monthly data
        assert elapsed < 0.5, f"Calendar year trend took {elapsed:.2f}s (target: <0.5s)"

        # Verify result
        assert len(collected) == 1
        row = collected.row(0, named=True)
        assert row["slope"] > 0
        assert row["duration_years"] >= 9.0  # ~10 years of data
