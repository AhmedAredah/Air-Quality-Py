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

from air_quality.modules import RowCountModule


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
    assert "row_count" in module.results
    assert module.results["row_count"] == 10


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
    assert "_elapsed_seconds" in module.results
    assert isinstance(module.results["_elapsed_seconds"], float)
    assert module.results["_elapsed_seconds"] >= 0.0
    # Should complete quickly (< 5 seconds)
    assert module.results["_elapsed_seconds"] < 5.0


def test_logging_with_config_warning():
    """Test that unexpected config logging doesn't crash the module."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=5, freq="h"),
            "site_id": ["G"] * 5,
            "pollutant": ["NO2"] * 5,
            "conc": range(5),
        }
    )

    # RowCountModule doesn't use config, so this should log warning
    config = {"unexpected_param": 42}
    # If warning logging causes issues, this will raise an exception
    module = RowCountModule.from_dataframe(df, config=config)

    # Verify module was created successfully despite warning
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
    assert "row_count" in module.results
    assert "qc_zero_rows" in module.results
    assert module.results["row_count"] == 8
    assert module.results["qc_zero_rows"] is False


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
    assert module1.results["row_count"] == 5
    assert module2.results["row_count"] == 7
