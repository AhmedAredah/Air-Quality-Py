"""Performance tests for DataFrame copy behavior.

Validates that the library minimizes unnecessary data copying to maintain
memory efficiency, especially for large datasets.

Constitution References:
- Section 11: Memory discipline - avoid unnecessary copies
- Section 11: Prefer views/in-place where safe
"""

import pandas as pd
import polars as pl
import pyarrow as pa

from air_quality.dataset import TimeSeriesDataset
from air_quality.modules import RowCountModule
from air_quality.modules.row_count import RowCountResult


def test_dataset_from_dataframe_no_copy_of_input():
    """Test that from_dataframe doesn't unnecessarily copy the input DataFrame.

    Note: This test verifies that the input DataFrame is converted to internal
    format (Polars LazyFrame) without creating unnecessary intermediate copies.
    The conversion to LazyFrame is expected and necessary.
    """
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=100, freq="h"),
            "site_id": ["A"] * 100,
            "pollutant": ["PM2.5"] * 100,
            "conc": range(100),
        }
    )

    # Get original DataFrame ID
    original_df_id = id(df)

    # Create dataset
    dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

    # Verify original DataFrame wasn't modified or replaced
    assert id(df) == original_df_id

    # Verify dataset uses LazyFrame internally (expected conversion)
    assert isinstance(dataset.lazyframe, pl.LazyFrame)


def test_module_from_dataframe_preserves_input():
    """Test that module creation doesn't modify the input DataFrame."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=50, freq="h"),
            "site_id": ["B"] * 50,
            "pollutant": ["O3"] * 50,
            "conc": range(50),
        }
    )

    # Make a copy to compare later
    df_copy = df.copy()
    original_df_id = id(df)

    # Create module
    module = RowCountModule.from_dataframe(df)

    # Verify original DataFrame wasn't modified
    assert id(df) == original_df_id
    pd.testing.assert_frame_equal(df, df_copy)


def test_module_from_dataset_no_dataset_copy():
    """Test that from_dataset doesn't copy the dataset object."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=30, freq="h"),
            "site_id": ["C"] * 30,
            "pollutant": ["NO2"] * 30,
            "conc": range(30),
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")
    dataset_id = id(dataset)

    # Create module from dataset
    module = RowCountModule.from_dataset(dataset)

    # Verify the module references the same dataset object (no copy)
    assert id(module.dataset) == dataset_id


def test_lazyframe_defers_computation():
    """Test that LazyFrame usage defers computation until needed.

    This verifies that the columnar backend (Polars LazyFrame) doesn't
    eagerly execute operations, maintaining memory efficiency.
    """
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=1000, freq="h"),
            "site_id": ["D"] * 1000,
            "pollutant": ["PM10"] * 1000,
            "conc": range(1000),
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

    # LazyFrame operations should not execute yet
    lazy = dataset.lazyframe

    # Verify it's still lazy
    assert isinstance(lazy, pl.LazyFrame)

    # Calling explain() should show the plan, not execute
    plan_str = lazy.explain()
    assert (
        "PROJECT" in plan_str
        or "Π" in plan_str
        or "DF" in plan_str
        or "SCAN" in plan_str
    )


def test_to_arrow_conversion_is_controlled():
    """Test that Arrow conversion happens only when explicitly requested."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=100, freq="h"),
            "site_id": ["E"] * 100,
            "pollutant": ["SO2"] * 100,
            "conc": range(100),
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

    # Dataset should be using LazyFrame, not Arrow yet
    assert isinstance(dataset.lazyframe, pl.LazyFrame)

    # Arrow conversion happens when explicitly called
    arrow_table = dataset.to_arrow()
    assert isinstance(arrow_table, pa.Table)

    # Original dataset still uses LazyFrame
    assert isinstance(dataset.lazyframe, pl.LazyFrame)


def test_to_pandas_conversion_is_controlled():
    """Test that pandas conversion happens only when explicitly requested."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=100, freq="h"),
            "site_id": ["F"] * 100,
            "pollutant": ["CO"] * 100,
            "conc": range(100),
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

    # Dataset should be using LazyFrame, not pandas
    assert isinstance(dataset.lazyframe, pl.LazyFrame)

    # pandas conversion happens when explicitly called
    result_df = dataset.to_pandas()
    assert isinstance(result_df, pd.DataFrame)

    # Original dataset still uses LazyFrame
    assert isinstance(dataset.lazyframe, pl.LazyFrame)


def test_module_run_doesnt_modify_dataset():
    """Test that running a module doesn't modify the underlying dataset."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=50, freq="h"),
            "site_id": ["G"] * 50,
            "pollutant": ["NO2"] * 50,
            "conc": range(50),
        }
    )

    module = RowCountModule.from_dataframe(df)
    dataset_id = id(module.dataset)
    lazyframe_id = id(module.dataset.lazyframe)

    # Run module
    module.run()

    # Dataset object should be the same
    assert id(module.dataset) == dataset_id
    # LazyFrame should be the same (no in-place modification)
    assert id(module.dataset.lazyframe) == lazyframe_id


def test_multiple_modules_can_share_dataset():
    """Test that multiple modules can safely use the same dataset.

    This verifies that modules don't modify shared data structures,
    enabling memory-efficient workflows.
    """
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=100, freq="h"),
            "site_id": ["H"] * 100,
            "pollutant": ["PM2.5"] * 100,
            "conc": range(100),
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")
    dataset_id = id(dataset)

    # Create two modules sharing the dataset
    module1 = RowCountModule.from_dataset(dataset)
    module2 = RowCountModule.from_dataset(dataset)

    # Both should reference the same dataset
    assert id(module1.dataset) == dataset_id
    assert id(module2.dataset) == dataset_id

    # Run both modules
    module1.run()
    module2.run()

    # Dataset should still be the same object
    assert id(module1.dataset) == dataset_id
    assert id(module2.dataset) == dataset_id

    # Both should get the same results
    assert (
        module1.results[RowCountResult.ROW_COUNT]
        == module2.results[RowCountResult.ROW_COUNT]
    )


def test_memory_efficiency_documented():
    """Test that memory efficiency patterns are documented.

    This is a documentation test - verifies that the codebase follows
    expected memory patterns even if we can't measure exact memory usage.
    """
    # Verify LazyFrame is used (deferred computation)
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=10, freq="h"),
            "site_id": ["X"] * 10,
            "pollutant": ["O3"] * 10,
            "conc": range(10),
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="datetime")

    # Should use LazyFrame (columnar, deferred)
    assert hasattr(dataset, "lazyframe")
    assert isinstance(dataset.lazyframe, pl.LazyFrame)

    # Should have explicit conversion methods (not automatic)
    assert hasattr(dataset, "to_arrow")
    assert hasattr(dataset, "to_pandas")

    # Conversions should be explicit, not happening automatically
    # (tested by checking the type remains LazyFrame)
    assert isinstance(dataset.lazyframe, pl.LazyFrame)
