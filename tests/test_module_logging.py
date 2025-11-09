"""Tests for logging integration in module lifecycle.

Validates that logging during module execution:
- Doesn't crash the module
- Tracks elapsed time
- Works with and without configuration warnings

Note: These are smoke tests since capsys interferes with the structured logger's
StreamHandler. The actual log messages can be observed when running modules
outside the test suite.
"""

import pandas as pd

from air_quality.module import SystemResultKey
from air_quality.modules import RowCountModule
from air_quality.modules.row_count import RowCountResult


def test_logging_doesnt_crash_module_run():
    """Test that logging during module execution doesn't cause crashes."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=10, freq="h"),
            "site_id": ["A"] * 10,
            "pollutant": ["PM2.5"] * 10,
            "conc": range(10),
        }
    )

    module = RowCountModule.from_dataframe(df)
    # If logging causes issues, this will raise an exception
    module.run()

    # Verify module completed successfully
    assert module.results is not None
    assert RowCountResult.ROW_COUNT in module.results
    assert module.results[RowCountResult.ROW_COUNT] == 10


def test_logging_elapsed_time_tracked():
    """Test that elapsed time is tracked in results."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=20, freq="h"),
            "site_id": ["B"] * 20,
            "pollutant": ["O3"] * 20,
            "conc": range(20),
        }
    )

    module = RowCountModule.from_dataframe(df)
    module.run()

    # Elapsed time should be in results
    assert SystemResultKey.ELAPSED_SECONDS in module.results
    assert isinstance(module.results[SystemResultKey.ELAPSED_SECONDS], float)
    assert module.results[SystemResultKey.ELAPSED_SECONDS] >= 0.0
    # Should complete quickly (< 5 seconds)
    assert module.results[SystemResultKey.ELAPSED_SECONDS] < 5.0


def test_logging_with_config_warning():
    """Test that logging works even with empty config."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=5, freq="h"),
            "site_id": ["G"] * 5,
            "pollutant": ["NO2"] * 5,
            "conc": range(5),
        }
    )

    # RowCountModule uses Enum keys for config (empty config is valid)
    config = {}
    module = RowCountModule.from_dataframe(df, config=config)

    # Verify module was created successfully
    assert module is not None
    assert module.config == config


def test_logging_during_multiple_operations():
    """Test that logging during multiple operations works correctly."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=8, freq="h"),
            "site_id": ["D"] * 8,
            "pollutant": ["PM10"] * 8,
            "conc": range(8),
        }
    )

    module = RowCountModule.from_dataframe(df)
    # Run with all operations (should log for each operation)
    module.run()

    # Verify both operations completed
    assert RowCountResult.ROW_COUNT in module.results
    assert RowCountResult.QC_ZERO_ROWS in module.results
    assert module.results[RowCountResult.ROW_COUNT] == 8
    assert module.results[RowCountResult.QC_ZERO_ROWS] is False


def test_logging_works_across_module_instances():
    """Test that logging works for multiple module instances."""
    df1 = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=5, freq="h"),
            "site_id": ["X"] * 5,
            "pollutant": ["NO2"] * 5,
            "conc": range(5),
        }
    )

    df2 = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-02", periods=7, freq="h"),
            "site_id": ["Y"] * 7,
            "pollutant": ["SO2"] * 7,
            "conc": range(7),
        }
    )

    # Create and run first module
    module1 = RowCountModule.from_dataframe(df1)
    module1.run()

    # Create and run second module
    module2 = RowCountModule.from_dataframe(df2)
    module2.run()

    # Verify both modules completed successfully
    assert module1.results[RowCountResult.ROW_COUNT] == 5
    assert module2.results[RowCountResult.ROW_COUNT] == 7
