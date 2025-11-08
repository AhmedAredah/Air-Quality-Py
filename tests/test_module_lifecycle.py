"""Tests for module lifecycle and reporting.

Validates:
- Module construction from DataFrame and dataset
- run() execution and idempotence
- Dashboard report structure and content
- CLI report content and formatting
- Column mapping summary in reports
- Provenance attachment
- Enum-based operation selection
"""

import pandas as pd
import pytest

from air_quality.exceptions import ConfigurationError
from air_quality.modules import RowCountModule, RowCountOperation


def test_rowcount_from_dataframe_success():
    """Test successful module construction from DataFrame."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=10, freq="h"),
            "site_id": ["A"] * 10,
            "pollutant": ["PM2.5"] * 10,
            "conc": range(10),
        }
    )

    module = RowCountModule.from_dataframe(df)

    assert module.MODULE_NAME == "row_count"
    assert module.DOMAIN == "qc"
    assert module.dataset.n_rows == 10
    assert not module._has_run


def test_rowcount_from_dataset_success():
    """Test module construction from existing dataset."""
    from air_quality.dataset import TimeSeriesDataset

    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=5, freq="h"),
            "site_id": ["B"] * 5,
            "pollutant": ["O3"] * 5,
            "conc": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )

    dataset = TimeSeriesDataset.from_dataframe(df)
    module = RowCountModule.from_dataset(dataset)

    assert module.MODULE_NAME == "row_count"
    assert module.dataset.n_rows == 5


def test_rowcount_run_default_operations():
    """Test run() with default operations (all operations)."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=20, freq="h"),
            "site_id": ["A"] * 20,
            "pollutant": ["NO2"] * 20,
            "conc": range(20),
        }
    )

    module = RowCountModule.from_dataframe(df)
    result = module.run()

    # Should return self for chaining
    assert result is module

    # Results should be populated
    assert "row_count" in module.results
    assert module.results["row_count"] == 20
    assert "qc_zero_rows" in module.results
    assert module.results["qc_zero_rows"] is False

    # Provenance should be attached
    assert module.provenance is not None
    assert module.provenance.module_name == "row_count"
    assert module.provenance.domain == "qc"

    # Should mark as run
    assert module._has_run


def test_rowcount_run_specific_operations():
    """Test run() with specific enum-based operations."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=15, freq="h"),
            "site_id": ["C"] * 15,
            "pollutant": ["PM10"] * 15,
            "conc": range(15),
        }
    )

    module = RowCountModule.from_dataframe(df)

    # Run only COUNT_ROWS operation
    module.run(operations=[RowCountOperation.COUNT_ROWS])

    # COUNT_ROWS should have run
    assert "row_count" in module.results
    assert module.results["row_count"] == 15

    # QC_CHECK should also run via _post_process
    assert "qc_zero_rows" in module.results


def test_rowcount_run_idempotence():
    """Test that run() can only be called once (idempotence)."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=5, freq="h"),
            "site_id": ["A"] * 5,
            "pollutant": ["SO2"] * 5,
            "conc": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )

    module = RowCountModule.from_dataframe(df)
    module.run()

    # Second run() should raise error
    with pytest.raises(RuntimeError) as exc_info:
        module.run()

    assert "run() can only be called once" in str(exc_info.value)


def test_dashboard_report_structure():
    """Test dashboard report has required keys and structure."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=10, freq="h"),
            "site_id": ["A"] * 10,
            "pollutant": ["PM2.5"] * 10,
            "conc": range(10),
        }
    )

    module = RowCountModule.from_dataframe(df)
    module.run()

    dashboard = module.report_dashboard()

    # Check required keys (constitution Section 8)
    assert "module" in dashboard
    assert "domain" in dashboard
    assert "schema_version" in dashboard
    assert "provenance" in dashboard
    assert "metrics" in dashboard

    # Check values
    assert dashboard["module"] == "row_count"
    assert dashboard["domain"] == "qc"
    assert dashboard["schema_version"] == "1.0.0"

    # Check provenance dict
    prov = dashboard["provenance"]
    assert "module_name" in prov
    assert "run_timestamp" in prov
    assert "software_version" in prov
    assert "config_hash" in prov

    # Check metrics
    metrics = dashboard["metrics"]
    assert "row_count" in metrics
    assert metrics["row_count"] == 10
    assert "qc_zero_rows" in metrics
    assert metrics["qc_zero_rows"] is False


def test_dashboard_report_before_run_raises():
    """Test that dashboard report raises if called before run()."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=5, freq="h"),
            "site_id": ["A"] * 5,
            "pollutant": ["NO2"] * 5,
            "conc": range(5),
        }
    )

    module = RowCountModule.from_dataframe(df)

    with pytest.raises(RuntimeError) as exc_info:
        module.report_dashboard()

    assert "must call run() before" in str(exc_info.value)


def test_cli_report_content():
    """Test CLI report contains expected content."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=8, freq="h"),
            "site_id": ["X"] * 8,
            "pollutant": ["O3"] * 8,
            "conc": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0],
        }
    )

    module = RowCountModule.from_dataframe(df)
    module.run()

    cli_report = module.report_cli()

    # Check content (constitution Section 8: inputs, methods, results, mapping)
    assert "row_count" in cli_report.lower()
    assert "Module: row_count" in cli_report
    assert "Domain: qc" in cli_report
    assert "Input Dataset:" in cli_report
    assert "Rows: 8" in cli_report
    assert "Row Count Analysis:" in cli_report
    assert "Total Rows: 8" in cli_report
    assert "Quality Control:" in cli_report
    assert "PASS" in cli_report or "✓" in cli_report

    # Check provenance section
    assert "Provenance:" in cli_report
    assert "Run Timestamp:" in cli_report
    assert "Software Version:" in cli_report
    assert "Config Hash:" in cli_report


def test_cli_report_column_mapping_summary():
    """Test CLI report includes column mapping summary."""
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range(
                "2024-01-01", periods=5, freq="h"
            ),  # Maps to datetime
            "station_id": ["A", "B", "C", "D", "E"],  # Maps to site_id
            "species": ["PM2.5"] * 5,  # Maps to pollutant
            "value": [1.0, 2.0, 3.0, 4.0, 5.0],  # Maps to conc
        }
    )

    module = RowCountModule.from_dataframe(df)
    module.run()

    cli_report = module.report_cli()

    # Check mapping summary (constitution Section 3: mapping in reports)
    assert "Column Mapping:" in cli_report
    assert "datetime <- timestamp" in cli_report
    assert "site_id <- station_id" in cli_report
    assert "pollutant <- species" in cli_report
    assert "conc <- value" in cli_report


def test_cli_report_before_run_raises():
    """Test that CLI report raises if called before run()."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=3, freq="h"),
            "site_id": ["A"] * 3,
            "pollutant": ["PM2.5"] * 3,
            "conc": [5.0, 10.0, 15.0],
        }
    )

    module = RowCountModule.from_dataframe(df)

    with pytest.raises(RuntimeError) as exc_info:
        module.report_cli()

    assert "must call run() before" in str(exc_info.value)


def test_provenance_populated_after_run():
    """Test provenance is properly populated after run()."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=12, freq="h"),
            "site_id": ["A"] * 12,
            "pollutant": ["NO2"] * 12,
            "conc": range(12),
        }
    )

    config = {"some_param": 42}
    module = RowCountModule.from_dataframe(df, config=config)
    module.run()

    prov = module.provenance
    assert prov is not None
    assert prov.module_name == "row_count"
    assert prov.domain == "qc"
    assert prov.config_hash is not None
    assert prov.run_timestamp is not None
    assert prov.software_version is not None

    # Check elapsed time recorded
    assert "_elapsed_seconds" in module.results
    assert module.results["_elapsed_seconds"] >= 0


def test_enum_operation_selection():
    """Test that enum-based operation selection works correctly."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=10, freq="h"),
            "site_id": ["A"] * 10,
            "pollutant": ["PM2.5"] * 10,
            "conc": range(10),
        }
    )

    module = RowCountModule.from_dataframe(df)

    # Test with only one operation
    module.run(operations=[RowCountOperation.COUNT_ROWS])

    assert "row_count" in module.results
    assert module.results["row_count"] == 10

    # QC should be added by _post_process
    assert "qc_zero_rows" in module.results


def test_config_validation_warning():
    """Test config validation handles unexpected parameters with warning."""
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=5, freq="h"),
            "site_id": ["A"] * 5,
            "pollutant": ["O3"] * 5,
            "conc": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )

    # RowCountModule doesn't use config but should accept it with warning
    config = {"unused_param": 123}
    module = RowCountModule.from_dataframe(df, config=config)

    # Should construct successfully (warning logged)
    assert module.config == config
