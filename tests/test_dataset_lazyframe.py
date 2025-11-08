"""Tests for LazyFrame internal storage validation.

Validates:
- Internal storage is Polars LazyFrame (not eager DataFrame)
- Operations remain lazy until explicit collection
- Lazy plan exists for chained operations
"""

import pandas as pd
import polars as pl
import pytest

from air_quality.dataset import TimeSeriesDataset


def test_internal_storage_is_lazyframe():
    """Test that internal storage uses Polars LazyFrame, not eager DataFrame."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=100, freq="h"),
            "site_id": ["A"] * 100,
            "pollutant": ["PM2.5"] * 100,
            "conc": range(100),
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df)

    # Internal data should be LazyFrame
    assert isinstance(dataset.lazyframe, pl.LazyFrame)
    # Not an eager DataFrame
    assert not isinstance(dataset.lazyframe, pl.DataFrame)


def test_lazyframe_plan_exists():
    """Test that LazyFrame has a query plan (lazy operations not executed)."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=50, freq="h"),
            "site_id": ["A"] * 50,
            "pollutant": ["O3"] * 50,
            "conc": range(50),
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df)
    lazy = dataset.lazyframe

    # LazyFrame should have a query plan
    # We can verify this by checking that explain() returns a plan description
    plan_str = lazy.explain()
    assert isinstance(plan_str, str)
    assert len(plan_str) > 0
    # Plan should mention dataframe operations (Polars uses "DF" or similar)
    assert any(keyword in plan_str.upper() for keyword in ["DF", "FILTER", "PROJECT"])


def test_chained_operations_remain_lazy():
    """Test that chained operations on LazyFrame remain lazy."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=1000, freq="h"),
            "site_id": ["A"] * 500 + ["B"] * 500,
            "pollutant": ["PM2.5"] * 1000,
            "conc": range(1000),
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df)

    # Chain some operations without collecting
    lazy_filtered = dataset.lazyframe.filter(pl.col("site_id") == "A")
    lazy_selected = lazy_filtered.select(["datetime", "conc"])

    # These should still be LazyFrame
    assert isinstance(lazy_filtered, pl.LazyFrame)
    assert isinstance(lazy_selected, pl.LazyFrame)

    # Verify the plan has increased complexity (multiple steps)
    plan = lazy_selected.explain()
    assert "FILTER" in plan.upper() or "filter" in plan.lower()
    # Polars uses "PROJECT" or "Π" (pi symbol) for column selection
    assert "PROJECT" in plan.upper() or "Π" in plan or "π" in plan

    # Only when we collect should we get eager DataFrame
    collected = lazy_selected.collect()
    assert isinstance(collected, pl.DataFrame)
    assert len(collected) == 500  # Half the original rows (site_id == 'A')


def test_lazy_vs_eager_memory_behavior():
    """Test that LazyFrame operations don't immediately materialize data.

    This is a conceptual test - LazyFrame defers execution until collect().
    """
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=10000, freq="h"),
            "site_id": ["A"] * 10000,
            "pollutant": ["NO2"] * 10000,
            "conc": range(10000),
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df)

    # Create a complex lazy computation chain
    lazy_result = (
        dataset.lazyframe.filter(pl.col("conc") > 5000)
        .select(["datetime", "site_id", "conc"])
        .sort("conc")
        .head(100)
    )

    # Should still be lazy
    assert isinstance(lazy_result, pl.LazyFrame)

    # Plan should show all operations
    plan = lazy_result.explain()
    # Check for multiple operation stages in the plan
    assert len(plan) > 100  # Complex plans tend to be verbose

    # Now collect and verify result
    result_df = lazy_result.collect()
    assert isinstance(result_df, pl.DataFrame)
    assert len(result_df) == 100


def test_lazyframe_schema_available_without_collection():
    """Test that schema can be accessed without triggering collection."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=10, freq="h"),
            "site_id": ["A"] * 10,
            "pollutant": ["PM2.5"] * 10,
            "conc": [float(i) for i in range(10)],
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df)

    # Schema should be accessible via collect_schema() without full collection
    schema = dataset.lazyframe.collect_schema()

    assert "datetime" in schema.names()
    assert "site_id" in schema.names()
    assert "conc" in schema.names()

    # Also test the dataset.schema property
    dataset_schema = dataset.schema
    assert isinstance(dataset_schema, dict)
    assert "datetime" in dataset_schema
    assert "conc" in dataset_schema
