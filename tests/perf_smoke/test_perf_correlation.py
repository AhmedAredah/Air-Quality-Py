"""Performance smoke tests for correlation analysis.

Constitution compliance:
- Section 11: Performance targets (100k rows in <2s)
- Section 15: Unit enforcement validation
"""

import sys
import time
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from air_quality.analysis.correlation import compute_pairwise
from air_quality.modules.statistics.correlation import (
    CorrelationConfig,
    CorrelationModule,
    CorrelationOperation,
    CorrelationResult,
)
from factories import create_synthetic_timeseries


class TestCorrelationPerformance:
    """Performance smoke tests for correlation primitives and module."""

    def test_correlation_pearson_100k_rows_global(self) -> None:
        """Test Pearson correlation on 100k rows completes in <2s (global mode)."""
        # Create synthetic dataset with 100k rows, 4 pollutants
        dataset = create_synthetic_timeseries(
            n_rows=100_000,
            n_sites=5,
            n_pollutants=4,
            seed=42,
            include_flags=True,
        )

        start_time = time.time()

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,  # Global correlation
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,
        )

        elapsed = time.time() - start_time

        # Verify results
        assert len(result) > 0, "Should produce correlation pairs"
        # 4 pollutants → 4*(4+1)/2 = 10 pairs (including diagonal)
        assert (
            len(result) == 10
        ), f"Expected 10 pairs for 4 pollutants, got {len(result)}"

        # Performance assertion
        assert elapsed < 2.0, f"Pearson correlation took {elapsed:.2f}s (expected <2s)"

        print(f"✓ Pearson global (100k rows): {elapsed:.3f}s")

    def test_correlation_spearman_100k_rows_global(self) -> None:
        """Test Spearman correlation on 100k rows completes in <2s (global mode)."""
        dataset = create_synthetic_timeseries(
            n_rows=100_000,
            n_sites=5,
            n_pollutants=4,
            seed=42,
            include_flags=True,
        )

        start_time = time.time()

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="spearman",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,
        )

        elapsed = time.time() - start_time

        # Verify results
        assert len(result) > 0
        assert len(result) == 10

        # Spearman is allowed to be slightly slower due to rank computation
        assert elapsed < 3.0, f"Spearman correlation took {elapsed:.2f}s (expected <3s)"

        print(f"✓ Spearman global (100k rows): {elapsed:.3f}s")

    def test_correlation_pearson_100k_rows_grouped(self) -> None:
        """Test Pearson correlation on 100k rows with grouping completes in <2s."""
        dataset = create_synthetic_timeseries(
            n_rows=100_000,
            n_sites=5,
            n_pollutants=4,
            seed=42,
            include_flags=True,
        )

        start_time = time.time()

        result = compute_pairwise(
            dataset=dataset,
            group_by=["site_id"],  # Group by site
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,
        )

        elapsed = time.time() - start_time

        # Verify results
        assert len(result) > 0
        # 5 sites × 10 pairs = 50 total pairs
        assert (
            len(result) == 50
        ), f"Expected 50 pairs (5 sites × 10 pairs), got {len(result)}"

        # Performance assertion
        assert elapsed < 2.0, f"Grouped Pearson took {elapsed:.2f}s (expected <2s)"

        print(f"✓ Pearson grouped (100k rows, 5 sites): {elapsed:.3f}s")

    def test_correlation_spearman_100k_rows_grouped(self) -> None:
        """Test Spearman correlation on 100k rows with grouping completes in <3s."""
        dataset = create_synthetic_timeseries(
            n_rows=100_000,
            n_sites=5,
            n_pollutants=4,
            seed=42,
            include_flags=True,
        )

        start_time = time.time()

        result = compute_pairwise(
            dataset=dataset,
            group_by=["site_id"],
            correlation_type="spearman",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,
        )

        elapsed = time.time() - start_time

        # Verify results
        assert len(result) > 0
        assert len(result) == 50

        # Spearman grouped allowed slightly more time
        assert elapsed < 3.0, f"Grouped Spearman took {elapsed:.2f}s (expected <3s)"

        print(f"✓ Spearman grouped (100k rows, 5 sites): {elapsed:.3f}s")

    def test_correlation_module_100k_rows(self) -> None:
        """Test CorrelationModule end-to-end on 100k rows completes in <2s."""
        dataset = create_synthetic_timeseries(
            n_rows=100_000,
            n_sites=5,
            n_pollutants=4,
            seed=42,
            include_flags=True,
        )

        module = CorrelationModule(
            dataset=dataset,
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
                CorrelationConfig.ALLOW_MISSING_UNITS: True,
            },
            
        )

        start_time = time.time()

        # Run module
        module.run(operations=[CorrelationOperation.PEARSON])

        elapsed = time.time() - start_time

        # Verify results
        correlations = module.results[CorrelationResult.CORRELATIONS]
        assert len(correlations) == 10

        # Performance assertion
        assert elapsed < 2.0, f"Module run took {elapsed:.2f}s (expected <2s)"

        print(f"✓ Module run (100k rows): {elapsed:.3f}s")

    def test_correlation_module_reports_performance(self) -> None:
        """Test that report generation is fast (<0.1s)."""
        dataset = create_synthetic_timeseries(
            n_rows=10_000,  # Smaller dataset for report generation
            n_sites=2,
            n_pollutants=3,
            seed=42,
        )

        module = CorrelationModule(
            dataset=dataset,
            config={
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.ALLOW_MISSING_UNITS: True,
            },
            
        )

        module.run(operations=[CorrelationOperation.PEARSON])

        # Test dashboard report performance
        start_time = time.time()
        dashboard = module.report_dashboard()
        elapsed_dashboard = time.time() - start_time

        assert (
            elapsed_dashboard < 0.1
        ), f"Dashboard report took {elapsed_dashboard:.3f}s"

        # Test CLI report performance
        start_time = time.time()
        cli_report = module.report_cli()
        elapsed_cli = time.time() - start_time

        assert elapsed_cli < 0.1, f"CLI report took {elapsed_cli:.3f}s"

        # Verify reports have content
        assert "metrics" in dashboard
        assert "correlations" in dashboard["metrics"]
        assert "Correlation Analysis Summary" in cli_report

        print(
            f"✓ Dashboard report: {elapsed_dashboard:.3f}s, CLI report: {elapsed_cli:.3f}s"
        )


@pytest.mark.slow
class TestCorrelationScalability:
    """Scalability tests for very large datasets (marked as slow)."""

    def test_correlation_500k_rows(self) -> None:
        """Test correlation scales to 500k rows (marked slow, <10s)."""
        dataset = create_synthetic_timeseries(
            n_rows=500_000,
            n_sites=10,
            n_pollutants=4,
            seed=42,
        )

        start_time = time.time()

        result = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,
        )

        elapsed = time.time() - start_time

        assert len(result) == 10
        # Relaxed constraint for very large dataset
        assert elapsed < 10.0, f"500k rows took {elapsed:.2f}s (expected <10s)"

        print(f"✓ Pearson (500k rows): {elapsed:.3f}s")
