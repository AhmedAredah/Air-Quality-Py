"""Tests for dataset construction and conversions.

Validates:
- BaseDataset/TimeSeriesDataset construction from pandas/Arrow
- Conversions to Arrow/pandas retain schema & mapping metadata
- Error on empty input
- Error on missing time index
"""

import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

from air_quality.dataset import BaseDataset, TimeSeriesDataset
from air_quality.exceptions import DataValidationError, SchemaError


def test_timeseries_from_dataframe_success():
    """Test successful construction from pandas DataFrame."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=10, freq="h"),
            "site_id": ["A"] * 10,
            "pollutant": ["PM2.5"] * 10,
            "conc": range(10),
        }
    )

    metadata = {"source": "test"}
    mapping = {"datetime": "timestamp", "conc": "concentration"}

    dataset = TimeSeriesDataset.from_dataframe(df, metadata=metadata, mapping=mapping)

    assert dataset.n_rows == 10
    assert dataset.time_index_name == "datetime"
    assert dataset.metadata["source"] == "test"
    assert dataset.mapping == mapping
    assert "datetime" in dataset.schema
    assert "conc" in dataset.schema


def test_timeseries_from_arrow_success():
    """Test successful construction from PyArrow Table."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=5, freq="D"),
            "site_id": ["B"] * 5,
            "pollutant": ["O3"] * 5,
            "conc": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )
    table = pa.Table.from_pandas(df)

    dataset = TimeSeriesDataset.from_arrow(table)

    assert dataset.n_rows == 5
    assert dataset.time_index_name == "datetime"


def test_timeseries_missing_time_index_raises():
    """Test that missing time index column raises SchemaError."""
    df = pd.DataFrame(
        {"site_id": ["A", "B"], "pollutant": ["PM2.5", "PM2.5"], "conc": [10.0, 20.0]}
    )

    with pytest.raises(SchemaError) as exc_info:
        TimeSeriesDataset.from_dataframe(df)

    assert "datetime" in str(exc_info.value).lower()
    assert "requires" in str(exc_info.value).lower()


def test_timeseries_custom_time_index_name():
    """Test custom time index column name."""
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=3, freq="h"),
            "site_id": ["A"] * 3,
            "pollutant": ["NO2"] * 3,
            "conc": [5.0, 6.0, 7.0],
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df, time_index_name="timestamp")

    assert dataset.time_index_name == "timestamp"
    assert dataset.n_rows == 3


def test_empty_dataset_raises():
    """Test that empty DataFrame raises DataValidationError."""
    df = pd.DataFrame(
        {"datetime": pd.DatetimeIndex([]), "site_id": [], "pollutant": [], "conc": []}
    )

    with pytest.raises(DataValidationError) as exc_info:
        TimeSeriesDataset.from_dataframe(df)

    assert "empty" in str(exc_info.value).lower()


def test_to_arrow_conversion():
    """Test conversion to PyArrow Table retains schema."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=3, freq="h"),
            "site_id": ["A", "B", "C"],
            "pollutant": ["PM2.5"] * 3,
            "conc": [10.0, 20.0, 30.0],
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df)
    arrow_table = dataset.to_arrow()

    assert isinstance(arrow_table, pa.Table)
    assert arrow_table.num_rows == 3
    assert "datetime" in arrow_table.column_names
    assert "conc" in arrow_table.column_names


def test_to_pandas_conversion():
    """Test conversion to pandas DataFrame retains schema."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=4, freq="D"),
            "site_id": ["X"] * 4,
            "pollutant": ["NO2"] * 4,
            "conc": [1.0, 2.0, 3.0, 4.0],
        }
    )

    mapping = {"datetime": "dt", "conc": "value"}
    dataset = TimeSeriesDataset.from_dataframe(df, mapping=mapping)
    result_df = dataset.to_pandas()

    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df) == 4
    assert list(result_df.columns) == ["datetime", "site_id", "pollutant", "conc"]
    # Mapping metadata preserved in dataset object
    assert dataset.mapping == mapping


def test_get_column():
    """Test retrieving a specific column."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=5, freq="h"),
            "site_id": ["A", "A", "B", "B", "C"],
            "pollutant": ["PM2.5"] * 5,
            "conc": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df)
    conc_series = dataset.get_column("conc")

    assert isinstance(conc_series, pl.Series)
    assert len(conc_series) == 5
    assert conc_series.to_list() == [1.0, 2.0, 3.0, 4.0, 5.0]


def test_get_column_missing_raises():
    """Test that requesting non-existent column raises KeyError."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=2, freq="h"),
            "site_id": ["A", "B"],
            "pollutant": ["O3", "O3"],
            "conc": [10.0, 20.0],
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df)

    with pytest.raises(KeyError) as exc_info:
        dataset.get_column("nonexistent")

    assert "nonexistent" in str(exc_info.value)


def test_dataset_id_metadata():
    """Test dataset_id retrieval from metadata."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=2, freq="h"),
            "site_id": ["A", "B"],
            "pollutant": ["PM2.5", "PM2.5"],
            "conc": [5.0, 10.0],
        }
    )

    metadata = {"dataset_id": "test-dataset-001", "source": "EPA"}
    dataset = TimeSeriesDataset.from_dataframe(df, metadata=metadata)

    assert dataset.get_dataset_id() == "test-dataset-001"


def test_dataset_id_none_if_missing():
    """Test that dataset_id returns None if not in metadata."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=2, freq="h"),
            "site_id": ["A", "B"],
            "pollutant": ["NO2", "NO2"],
            "conc": [3.0, 4.0],
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df)

    assert dataset.get_dataset_id() is None


def test_is_empty_method():
    """Test is_empty() method (should always be False after construction)."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=1, freq="h"),
            "site_id": ["A"],
            "pollutant": ["PM2.5"],
            "conc": [15.0],
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df)

    # Should not be empty since we validated in constructor
    assert not dataset.is_empty()


def test_lazyframe_property():
    """Test accessing internal LazyFrame."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=3, freq="h"),
            "site_id": ["A"] * 3,
            "pollutant": ["O3"] * 3,
            "conc": [1.0, 2.0, 3.0],
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df)
    lazy = dataset.lazyframe

    assert isinstance(lazy, pl.LazyFrame)
    # Should remain lazy until collection
    collected = lazy.collect()
    assert len(collected) == 3
