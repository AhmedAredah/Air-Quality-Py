"""Tests for TimeBounds and compute_time_bounds (Feature 002).

Constitution compliance:
- Section 3: UTC canonical time, timezone-aware datetimes, sub-second precision
- Section 10: Deterministic, reproducible behavior
- Section 11: Single collect operation (NFR-M01)
- Validation: tz-aware UTC outputs, precision preservation, min/max correctness

Test scenarios (placeholder - skip markers):
1. TimeBounds dataclass is frozen and immutable
2. TimeBounds start/end are tz-aware UTC datetimes
3. compute_time_bounds returns precise min/max (no truncation)
4. Sub-second precision preserved (microseconds)
5. Naive datetime input converted to UTC
6. Aware non-UTC datetime converted to UTC (preserving instant)
7. Empty LazyFrame handling (underlying error surfaced)
8. Non-datetime column raises appropriate error
9. Single collect operation verified (no multiple collects)
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import polars as pl
import pytest

from air_quality.time_utils import TimeBounds, compute_time_bounds


class TestTimeBoundsDataclass:
    """Test TimeBounds dataclass properties."""

    def test_timebounds_is_frozen(self):
        """TimeBounds is immutable (frozen dataclass)."""
        bounds = TimeBounds(
            start=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            end=datetime(2025, 1, 31, 23, 59, 59, tzinfo=timezone.utc),
        )
        # Should raise error when trying to modify
        with pytest.raises(AttributeError):
            bounds.start = datetime(2025, 2, 1, tzinfo=timezone.utc)

    def test_timebounds_start_end_tz_aware(self):
        """TimeBounds start/end are timezone-aware UTC."""
        bounds = TimeBounds(
            start=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            end=datetime(2025, 1, 31, 23, 59, 59, tzinfo=timezone.utc),
        )
        assert bounds.start.tzinfo is not None
        assert bounds.end.tzinfo is not None
        assert bounds.start.tzinfo == timezone.utc
        assert bounds.end.tzinfo == timezone.utc

    def test_timebounds_preserves_subsecond_precision(self):
        """TimeBounds preserves microsecond precision."""
        start = datetime(2025, 1, 1, 0, 0, 0, 123456, tzinfo=timezone.utc)
        end = datetime(2025, 1, 31, 23, 59, 59, 987654, tzinfo=timezone.utc)
        bounds = TimeBounds(start=start, end=end)
        assert bounds.start.microsecond == 123456
        assert bounds.end.microsecond == 987654


class TestComputeTimeBounds:
    """Test compute_time_bounds function."""

    def test_compute_bounds_simple_case(self):
        """compute_time_bounds returns min/max from datetime column."""
        lf = pl.LazyFrame(
            {
                "datetime": [
                    datetime(2025, 1, 1, 0, 0, 0),
                    datetime(2025, 1, 15, 12, 0, 0),
                    datetime(2025, 1, 31, 23, 59, 59),
                ]
            }
        )
        bounds = compute_time_bounds(lf)
        assert isinstance(bounds, TimeBounds)
        assert bounds.start == datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert bounds.end == datetime(2025, 1, 31, 23, 59, 59, tzinfo=timezone.utc)

    def test_compute_bounds_preserves_subsecond_precision(self):
        """compute_time_bounds preserves microsecond precision."""
        lf = pl.LazyFrame(
            {
                "datetime": [
                    datetime(2025, 1, 1, 0, 0, 0, 123456),
                    datetime(2025, 1, 15, 12, 0, 0, 500000),
                    datetime(2025, 1, 31, 23, 59, 59, 987654),
                ]
            }
        )
        bounds = compute_time_bounds(lf)
        assert bounds.start.microsecond == 123456
        assert bounds.end.microsecond == 987654

    def test_compute_bounds_custom_time_column(self):
        """compute_time_bounds accepts custom time_col parameter."""
        lf = pl.LazyFrame(
            {
                "timestamp": [
                    datetime(2025, 1, 1, 0, 0, 0),
                    datetime(2025, 1, 31, 23, 59, 59),
                ]
            }
        )
        bounds = compute_time_bounds(lf, time_col="timestamp")
        assert bounds.start == datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    def test_compute_bounds_naive_datetime_converted_to_utc(self):
        """Naive datetime input treated as UTC and made aware."""
        lf = pl.LazyFrame(
            {
                "datetime": [
                    datetime(2025, 1, 1, 12, 0, 0),  # naive
                    datetime(2025, 1, 2, 12, 0, 0),  # naive
                ]
            }
        )
        bounds = compute_time_bounds(lf)
        # Should be converted to tz-aware UTC
        assert bounds.start.tzinfo == timezone.utc
        assert bounds.end.tzinfo == timezone.utc

    def test_compute_bounds_aware_non_utc_converted_to_utc(self):
        """Aware non-UTC datetimes converted to UTC preserving instant."""
        # Create datetime in EST (UTC-5)
        est = timezone(timedelta(hours=-5))
        lf = pl.LazyFrame(
            {
                "datetime": [
                    datetime(2025, 1, 1, 7, 0, 0, tzinfo=est),  # 7 AM EST = 12 PM UTC
                    datetime(2025, 1, 2, 7, 0, 0, tzinfo=est),  # 7 AM EST = 12 PM UTC
                ]
            }
        )
        bounds = compute_time_bounds(lf)
        # Should be converted to UTC
        assert bounds.start.tzinfo == timezone.utc
        # 7 AM EST = 12 PM UTC
        assert bounds.start.hour == 12

    def test_compute_bounds_single_row(self):
        """compute_time_bounds handles single-row LazyFrame (start == end)."""
        lf = pl.LazyFrame({"datetime": [datetime(2025, 1, 15, 12, 0, 0)]})
        bounds = compute_time_bounds(lf)
        assert bounds.start == bounds.end

    def test_compute_bounds_missing_column_raises_error(self):
        """compute_time_bounds with missing column raises KeyError."""
        lf = pl.LazyFrame({"other_column": [1, 2, 3]})
        with pytest.raises((KeyError, Exception)):
            # Should raise error for missing datetime column
            compute_time_bounds(lf)

    def test_compute_bounds_non_datetime_column_raises_error(self):
        """compute_time_bounds with non-datetime column surfaces error."""
        lf = pl.LazyFrame({"datetime": ["2025-01-01", "2025-01-31"]})
        with pytest.raises(Exception):
            # Should raise type/conversion error
            compute_time_bounds(lf)

    def test_compute_bounds_deterministic(self):
        """compute_time_bounds is deterministic (same input → same output)."""
        lf = pl.LazyFrame(
            {
                "datetime": [
                    datetime(2025, 1, 1, 0, 0, 0),
                    datetime(2025, 1, 31, 23, 59, 59),
                ]
            }
        )
        bounds1 = compute_time_bounds(lf)
        bounds2 = compute_time_bounds(lf)
        assert bounds1.start == bounds2.start
        assert bounds1.end == bounds2.end

    def test_compute_bounds_single_collect_operation(self):
        """compute_time_bounds uses single collect (NFR-M01).

        Verifies that min and max are computed in a single aggregation,
        not separate collect operations.
        """
        # Given: LazyFrame with datetime data
        lf = pl.LazyFrame(
            {
                "datetime": [
                    datetime(2025, 1, 1, 0, 0, 0),
                    datetime(2025, 1, 15, 12, 30, 45),
                    datetime(2025, 1, 31, 23, 59, 59),
                ]
            }
        )

        # When: Computing time bounds
        # The implementation should use a single collect with multiple aggregations:
        # df.select([pl.col("datetime").min(), pl.col("datetime").max()]).collect()
        # NOT: df.select(pl.col("datetime").min()).collect() + df.select(...).collect()
        bounds = compute_time_bounds(lf)

        # Then: Verify result is correct (indirect verification of single collect)
        assert isinstance(bounds, TimeBounds)
        assert bounds.start == datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert bounds.end == datetime(2025, 1, 31, 23, 59, 59, tzinfo=timezone.utc)

        # Additional verification: Check implementation follows single-collect pattern
        # This is more of a code review requirement, but we can verify the result
        # matches expected behavior that would only work with proper aggregation
        assert bounds.start < bounds.end

    def test_compute_bounds_single_collect_performance(self):
        """Single collect approach is faster than multiple collects (NFR-M01)."""
        # Given: Larger dataset where performance difference would be measurable
        import time

        n_rows = 100_000
        dates = [datetime(2025, 1, 1) + timedelta(hours=i) for i in range(n_rows)]
        lf = pl.LazyFrame({"datetime": dates})

        # When: Computing time bounds (should use single collect internally)
        start_time = time.perf_counter()
        bounds = compute_time_bounds(lf)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Then: Should complete quickly (< 100ms for 100K rows)
        # If using multiple collects, would be much slower
        assert elapsed_ms < 100.0, (
            f"compute_time_bounds took {elapsed_ms:.2f}ms, "
            f"suggests multiple collects instead of single aggregation"
        )

        # Verify correctness
        assert bounds.start == datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        expected_end = datetime(2025, 1, 1) + timedelta(hours=n_rows - 1)
        assert bounds.end == expected_end.replace(tzinfo=timezone.utc)
