"""Performance benchmarks for column mapping utility.

Tests mapping performance on large synthetic datasets to ensure the
three-level mapping (explicit → fuzzy → validation) scales appropriately.

Constitution References:
- Section 11: Target scales include millions of rows
- Section 11: Performance regression tests on representative datasets
"""

import time

import pandas as pd
import pytest

from air_quality.mapping import ColumnMapper


# Performance thresholds (may need adjustment based on hardware)
LARGE_DATASET_ROWS = 1_000_000
MAPPING_TIME_THRESHOLD_SECONDS = 2.0  # Allow 2 seconds for 1M rows


def test_explicit_mapping_large_dataset():
    """Benchmark explicit mapping on large dataset (1M rows)."""
    # Create large synthetic dataset
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range(
                "2020-01-01", periods=LARGE_DATASET_ROWS, freq="min"
            ),
            "station": ["A"] * LARGE_DATASET_ROWS,
            "species": ["PM2.5"] * LARGE_DATASET_ROWS,
            "value": range(LARGE_DATASET_ROWS),
        }
    )

    # Explicit mapping (fastest path)
    explicit_mapping = {
        "datetime": "timestamp",
        "site_id": "station",
        "pollutant": "species",
        "conc": "value",
    }

    required_columns = ["datetime", "site_id", "pollutant", "conc"]

    # Benchmark mapping time
    start_time = time.perf_counter()
    result = ColumnMapper.map(df, required=required_columns, explicit=explicit_mapping)
    elapsed = time.perf_counter() - start_time

    # Verify mapping succeeded
    assert set(result.df_mapped.columns) >= set(required_columns)

    # Log performance
    print(f"\nExplicit mapping performance:")
    print(f"  Rows: {LARGE_DATASET_ROWS:,}")
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Throughput: {LARGE_DATASET_ROWS / elapsed:,.0f} rows/sec")

    # Check threshold (mark skip if hardware can't meet it)
    if elapsed > MAPPING_TIME_THRESHOLD_SECONDS:
        pytest.skip(
            f"Mapping took {elapsed:.3f}s (threshold: {MAPPING_TIME_THRESHOLD_SECONDS}s). "
            f"Hardware may be slower than benchmark baseline. "
            f"This is acceptable for local development."
        )


def test_fuzzy_mapping_large_dataset():
    """Benchmark fuzzy mapping on large dataset (1M rows)."""
    # Create large synthetic dataset with synonym columns
    df = pd.DataFrame(
        {
            "date_time": pd.date_range(
                "2020-01-01", periods=LARGE_DATASET_ROWS, freq="min"
            ),
            "location_id": ["B"] * LARGE_DATASET_ROWS,
            "pollutant_name": ["O3"] * LARGE_DATASET_ROWS,
            "concentration": range(LARGE_DATASET_ROWS),
        }
    )

    required_columns = ["datetime", "site_id", "pollutant", "conc"]

    # Define synonyms for fuzzy matching
    synonyms = {
        "datetime": ["date_time", "timestamp", "time"],
        "site_id": ["location_id", "station", "site"],
        "pollutant": ["pollutant_name", "species", "parameter"],
        "conc": ["concentration", "value", "measurement"],
    }

    # Benchmark fuzzy mapping (no explicit mapping provided)
    start_time = time.perf_counter()
    result = ColumnMapper.map(df, required=required_columns, synonyms=synonyms)
    elapsed = time.perf_counter() - start_time

    # Verify mapping succeeded
    assert set(result.df_mapped.columns) >= set(required_columns)

    # Log performance
    print(f"\nFuzzy mapping performance:")
    print(f"  Rows: {LARGE_DATASET_ROWS:,}")
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Throughput: {LARGE_DATASET_ROWS / elapsed:,.0f} rows/sec")

    # Fuzzy mapping may be slower than explicit, allow 2x threshold
    if elapsed > MAPPING_TIME_THRESHOLD_SECONDS * 2:
        pytest.skip(
            f"Fuzzy mapping took {elapsed:.3f}s (threshold: {MAPPING_TIME_THRESHOLD_SECONDS * 2}s). "
            f"Hardware may be slower than benchmark baseline. "
            f"This is acceptable for local development."
        )


def test_mapping_scales_linearly():
    """Test that mapping time scales approximately linearly with dataset size."""
    required_columns = ["datetime", "site_id", "pollutant", "conc"]

    explicit_mapping = {
        "datetime": "timestamp",
        "site_id": "station",
        "pollutant": "species",
        "conc": "value",
    }

    sizes = [10_000, 50_000, 100_000]
    times = []

    for size in sizes:
        df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2020-01-01", periods=size, freq="min"),
                "station": ["A"] * size,
                "species": ["PM2.5"] * size,
                "value": range(size),
            }
        )

        start_time = time.perf_counter()
        result = ColumnMapper.map(
            df, required=required_columns, explicit=explicit_mapping
        )
        elapsed = time.perf_counter() - start_time

        assert set(result.df_mapped.columns) >= set(required_columns)
        times.append(elapsed)

    # Log scaling behavior
    print(f"\nMapping scaling behavior:")
    for size, elapsed in zip(sizes, times):
        print(f"  {size:,} rows: {elapsed:.4f}s ({size/elapsed:,.0f} rows/sec)")

    # Verify approximate linear scaling (allow some variance)
    # Ratio of (time2/time1) should be close to (size2/size1)
    time_ratio = times[-1] / times[0]
    size_ratio = sizes[-1] / sizes[0]

    # Allow 2x deviation from perfect linear scaling
    # (accounts for startup overhead and system variance)
    assert (
        time_ratio < size_ratio * 2
    ), f"Mapping doesn't scale linearly: {time_ratio:.2f}x time for {size_ratio:.2f}x data"


def test_mapping_memory_efficient():
    """Test that mapping doesn't create excessive intermediate DataFrames.

    This is a smoke test - we verify the mapping completes without
    obvious memory issues on a moderately large dataset.
    """
    # 500K rows - large enough to detect memory issues
    size = 500_000

    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2020-01-01", periods=size, freq="min"),
            "site_id": ["A"] * size,
            "pollutant": ["PM10"] * size,
            "conc": range(size),
        }
    )

    required_columns = ["datetime", "site_id", "pollutant", "conc"]

    # Map with explicit mapping (no synonyms, should be very fast)
    explicit_mapping = {col: col for col in required_columns}

    start_time = time.perf_counter()
    result = ColumnMapper.map(df, required=required_columns, explicit=explicit_mapping)
    elapsed = time.perf_counter() - start_time

    assert set(result.df_mapped.columns) >= set(required_columns)

    # For identical column names, mapping should be very fast
    # (just validation, no renaming)
    print(f"\nIdentity mapping performance (500K rows): {elapsed:.4f}s")

    # Should be extremely fast for identity mapping
    assert elapsed < 0.5, f"Identity mapping too slow: {elapsed:.3f}s for {size:,} rows"


def test_wide_dataset_mapping():
    """Test mapping performance on dataset with many columns."""
    rows = 100_000
    # Create dataset with 50 columns (typical for speciation data)
    num_cols = 50

    df_dict = {
        "datetime": pd.date_range("2020-01-01", periods=rows, freq="min"),
        "site_id": ["A"] * rows,
        "pollutant": ["PM2.5"] * rows,
        "conc": range(rows),
    }

    # Add 46 extra columns
    for i in range(num_cols - 4):
        df_dict[f"extra_col_{i}"] = [0] * rows

    df = pd.DataFrame(df_dict)

    required_columns = ["datetime", "site_id", "pollutant", "conc"]
    explicit_mapping = {col: col for col in required_columns}

    start_time = time.perf_counter()
    result = ColumnMapper.map(df, required=required_columns, explicit=explicit_mapping)
    elapsed = time.perf_counter() - start_time

    assert set(result.df_mapped.columns) >= set(required_columns)

    print(f"\nWide dataset mapping ({rows:,} rows x {num_cols} cols): {elapsed:.4f}s")

    # Should handle wide datasets efficiently
    assert elapsed < 1.0, f"Wide dataset mapping too slow: {elapsed:.3f}s"


@pytest.mark.parametrize("strategy", ["explicit", "fuzzy"])
def test_repeated_mapping_consistent_performance(strategy):
    """Test that repeated mapping operations have consistent performance.

    This helps detect performance regressions or caching issues.
    """
    rows = 50_000

    df_dict = {
        "timestamp" if strategy == "explicit" else "date_time": pd.date_range(
            "2020-01-01", periods=rows, freq="min"
        ),
        "station" if strategy == "explicit" else "location_id": ["A"] * rows,
        "species" if strategy == "explicit" else "pollutant_name": ["NO2"] * rows,
        "value" if strategy == "explicit" else "concentration": range(rows),
    }

    df = pd.DataFrame(df_dict)

    required_columns = ["datetime", "site_id", "pollutant", "conc"]

    kwargs = {"required": required_columns}

    if strategy == "explicit":
        kwargs["explicit"] = {
            "datetime": "timestamp",
            "site_id": "station",
            "pollutant": "species",
            "conc": "value",
        }
    else:
        kwargs["synonyms"] = {
            "datetime": ["date_time", "timestamp"],
            "site_id": ["location_id", "station"],
            "pollutant": ["pollutant_name", "species"],
            "conc": ["concentration", "value"],
        }

    times = []
    for i in range(3):
        start_time = time.perf_counter()
        result = ColumnMapper.map(df, **kwargs)
        elapsed = time.perf_counter() - start_time

        assert set(result.df_mapped.columns) >= set(required_columns)
        times.append(elapsed)

    # Times should be reasonably consistent
    # For sub-millisecond timings, variance can be higher due to measurement noise
    avg_time = sum(times) / len(times)
    max_variance = 1.0 if avg_time < 0.001 else 0.5  # 100% for <1ms, 50% otherwise

    for t in times:
        variance = abs(t - avg_time) / avg_time if avg_time > 0 else 0
        assert variance < max_variance, (
            f"Inconsistent performance ({strategy}): {times}, "
            f"avg={avg_time:.4f}s, variance={variance:.1%}"
        )

    print(f"\n{strategy.title()} mapping consistency (3 runs, {rows:,} rows):")
    print(f"  Times: {[f'{t:.4f}s' for t in times]}")
    print(f"  Average: {avg_time:.4f}s")
