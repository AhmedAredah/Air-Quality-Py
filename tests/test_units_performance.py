"""
Performance validation tests for unit conversion functions (Phase 10).

Feature 002: Units & Time Primitives
Phase: 10 (Performance Validation)

Tests verify O(n) vectorized performance targets per Constitution Section 11.

Constitution compliance:
- Sec 11: Vectorized operations, no row-wise Python loops, target performance
- NFR-P01: 1M row conversion < 50ms smoke test
"""

import time

import numpy as np
import pandas as pd
import polars as pl
import pytest

from air_quality.units import Unit, convert_values


class TestUnitConversionPerformance:
    """Test performance targets for vectorized unit conversion."""

    def test_1m_row_conversion_pandas_series_meets_target(self):
        """1M row conversion with pandas Series completes in < 50ms (NFR-P01)."""
        # Given: 1 million row pandas Series
        n_rows = 1_000_000
        values = pd.Series(np.random.uniform(10.0, 100.0, n_rows))

        # When: Converting from ug/m3 to mg/m3
        start_time = time.perf_counter()
        result = convert_values(values, Unit.UG_M3, Unit.MG_M3)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Then: Conversion completes in < 50ms
        assert elapsed_ms < 50.0, (
            f"1M row conversion took {elapsed_ms:.2f}ms, "
            f"exceeds 50ms target (NFR-P01)"
        )

        # Verify correctness (spot check)
        assert len(result) == n_rows
        assert isinstance(result, pd.Series)

    def test_1m_row_conversion_polars_series_meets_target(self):
        """1M row conversion with Polars Series completes in < 50ms (NFR-P01)."""
        # Given: 1 million row Polars Series
        n_rows = 1_000_000
        values = pl.Series("conc", np.random.uniform(10.0, 100.0, n_rows))

        # When: Converting from ppb to ppm
        start_time = time.perf_counter()
        result = convert_values(values, Unit.PPB, Unit.PPM)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Then: Conversion completes in < 50ms
        assert elapsed_ms < 50.0, (
            f"1M row Polars conversion took {elapsed_ms:.2f}ms, "
            f"exceeds 50ms target (NFR-P01)"
        )

        # Verify correctness (spot check)
        assert len(result) == n_rows
        assert isinstance(result, pl.Series)

    def test_conversion_performance_scales_linearly(self):
        """Verify O(n) scaling by comparing 100K vs 1M row conversion times."""
        # Given: Two datasets of different sizes
        small_size = 100_000
        large_size = 1_000_000
        small_values = pd.Series(np.random.uniform(10.0, 100.0, small_size))
        large_values = pd.Series(np.random.uniform(10.0, 100.0, large_size))

        # When: Converting both datasets
        start_small = time.perf_counter()
        convert_values(small_values, Unit.UG_M3, Unit.MG_M3)
        time_small = time.perf_counter() - start_small

        start_large = time.perf_counter()
        convert_values(large_values, Unit.UG_M3, Unit.MG_M3)
        time_large = time.perf_counter() - start_large

        # Then: Time ratio should be approximately size ratio (within 2x tolerance)
        # This verifies O(n) complexity, not worse
        size_ratio = large_size / small_size  # 10x
        time_ratio = time_large / time_small

        # Allow 2x tolerance for system variance (should be ~10x if O(n))
        assert time_ratio < size_ratio * 2.0, (
            f"Performance doesn't scale linearly: "
            f"{large_size/small_size}x data took {time_ratio:.1f}x time "
            f"(expected ~{size_ratio}x for O(n))"
        )

    def test_conversion_with_nans_no_performance_penalty(self):
        """NaN-heavy datasets don't cause significant performance degradation."""
        # Given: 1M row dataset with 50% NaNs
        n_rows = 1_000_000
        values = pd.Series(np.random.uniform(10.0, 100.0, n_rows))
        values[::2] = np.nan  # 50% NaN

        # When: Converting with NaNs
        start_time = time.perf_counter()
        result = convert_values(values, Unit.UG_M3, Unit.MG_M3)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Then: Still meets 50ms target (NaNs handled vectorized)
        assert elapsed_ms < 50.0, (
            f"1M row conversion with 50% NaNs took {elapsed_ms:.2f}ms, "
            f"exceeds 50ms target"
        )

        # Verify NaN preservation
        assert result.isna().sum() == values.isna().sum()


class TestPerformanceRegressionGuards:
    """Additional performance regression tests for critical paths."""

    def test_identity_conversion_is_optimized(self):
        """Identity conversion (same unit) should be near-instant."""
        # Given: Large dataset
        n_rows = 1_000_000
        values = pd.Series(np.random.uniform(10.0, 100.0, n_rows))

        # When: Identity conversion
        start_time = time.perf_counter()
        result = convert_values(values, Unit.UG_M3, Unit.UG_M3)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Then: Should be extremely fast (< 10ms due to optimization)
        assert elapsed_ms < 10.0, (
            f"Identity conversion took {elapsed_ms:.2f}ms, "
            f"suggests missing optimization"
        )

        # Verify same object returned (no copy)
        assert result is values

    def test_scalar_conversion_overhead_minimal(self):
        """Scalar conversions should have minimal overhead."""
        # Given: Single scalar value
        value = 42.5

        # When: Converting many times (to measure overhead)
        n_iterations = 10000
        start_time = time.perf_counter()
        for _ in range(n_iterations):
            convert_values(value, Unit.PPB, Unit.PPM)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Then: Each conversion should be < 0.01ms average
        avg_time_ms = elapsed_ms / n_iterations
        assert (
            avg_time_ms < 0.01
        ), f"Scalar conversion overhead {avg_time_ms:.4f}ms too high"

    @pytest.mark.slow
    def test_10m_row_conversion_completes_reasonably(self):
        """10M row conversion completes in reasonable time (< 500ms)."""
        # Given: 10 million row dataset
        n_rows = 10_000_000
        values = pd.Series(np.random.uniform(10.0, 100.0, n_rows))

        # When: Converting
        start_time = time.perf_counter()
        result = convert_values(values, Unit.UG_M3, Unit.MG_M3)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Then: Completes in < 500ms (5x the 1M target, showing linear scaling)
        assert elapsed_ms < 500.0, (
            f"10M row conversion took {elapsed_ms:.2f}ms, " f"exceeds reasonable limit"
        )

        assert len(result) == n_rows


class TestPerformanceDocumentation:
    """Tests that document actual performance characteristics for HANDOFF.md."""

    def test_measure_baseline_performance_metrics(self, capsys):
        """Measure and report baseline performance metrics."""
        # Test various sizes to document scaling
        test_sizes = [10_000, 100_000, 1_000_000]
        results = []

        for size in test_sizes:
            values = pd.Series(np.random.uniform(10.0, 100.0, size))

            # Measure conversion time
            start_time = time.perf_counter()
            convert_values(values, Unit.UG_M3, Unit.MG_M3)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            throughput = size / (elapsed_ms / 1000.0)  # rows/second
            results.append(
                {
                    "size": size,
                    "time_ms": elapsed_ms,
                    "throughput": throughput,
                }
            )

        # Report for documentation
        print("\n=== Feature 002 Performance Baseline ===")
        print("Unit Conversion (ug/m3 → mg/m3):")
        for r in results:
            print(
                f"  {r['size']:>10,} rows: {r['time_ms']:>6.2f}ms "
                f"({r['throughput']:>12,.0f} rows/sec)"
            )
        print("=" * 50)

        # Verify all meet targets
        for r in results:
            if r["size"] == 1_000_000:
                assert r["time_ms"] < 50.0, "1M row target not met"
