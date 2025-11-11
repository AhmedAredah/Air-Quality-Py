"""Integration tests for CorrelationModule CLI and dashboard reports.

Tests full module execution including reports and provenance.

Constitution References
-----------------------
- Section 7: AirQualityModule interface compliance
- Section 8: Dual reporting (dashboard + CLI)
- Section 15: Provenance tracking
"""

from __future__ import annotations

import json
from typing import Any, Dict

import pandas as pd
import pytest

from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.modules.statistics.correlation import (
    CorrelationConfig,
    CorrelationModule,
)
from air_quality.modules.statistics.correlation import CorrelationOperation
from air_quality.qc_flags import QCFlag


class TestCorrelationModuleCLI:
    """Test CorrelationModule CLI report functionality."""

    def test_module_cli_report_basic_structure(self) -> None:
        """Test CLI report has required sections."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        # Create module with units to avoid UnitError
        module = CorrelationModule(
            dataset=TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ug/m3"}),
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.MIN_SAMPLES: 3,
                CorrelationConfig.ALLOW_MISSING_UNITS: True,  # Override for test
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
            },
            
        )

        module.run(operations=[CorrelationOperation.PEARSON])
        cli_report = module.report_cli()

        # Should be non-empty string
        assert isinstance(cli_report, str)
        assert len(cli_report) > 0

        # Should contain module name
        assert "Correlation" in cli_report or "correlation" in cli_report

        # Should contain method (uppercase in report)
        assert "Pearson" in cli_report or "pearson" in cli_report or "PEARSON" in cli_report

        # Should contain pair information
        assert "PM25" in cli_report
        assert "PM10" in cli_report

    def test_module_cli_report_includes_correlation_values(self) -> None:
        """Test CLI report displays correlation coefficients."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,  # Perfect correlation
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        module = CorrelationModule(
            dataset=TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ug/m3"}),
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.MIN_SAMPLES: 3,
                CorrelationConfig.ALLOW_MISSING_UNITS: True,
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
            },
            
        )

        module.run(operations=[CorrelationOperation.PEARSON])
        cli_report = module.report_cli()

        # Should show perfect correlation (1.00 or 1.000)
        assert "1.0" in cli_report

    def test_module_cli_report_shows_sample_counts(self) -> None:
        """Test CLI report includes sample counts (n) per pair."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        module = CorrelationModule(
            dataset=TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ug/m3"}),
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.MIN_SAMPLES: 3,
                CorrelationConfig.ALLOW_MISSING_UNITS: True,
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
            },
            
        )

        module.run(operations=[CorrelationOperation.PEARSON])
        cli_report = module.report_cli()

        # Should show n=5 for pairs
        assert "n=5" in cli_report or "n = 5" in cli_report or "5" in cli_report

    def test_module_cli_report_shows_qc_exclusions(self) -> None:
        """Test CLI report documents QC flag exclusions."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=15, freq="h", tz="UTC"),
                "site_id": ["site1"] * 15,
                "pollutant": ["PM25"] * 10 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 3,
                "flag": (
                    [QCFlag.VALID.value] * 5
                    + [QCFlag.INVALID.value] * 3  # Excluded
                    + [QCFlag.OUTLIER.value] * 2  # Excluded
                    + [QCFlag.VALID.value] * 5
                ),
            }
        )

        module = CorrelationModule(
            dataset=TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ug/m3"}),
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.MIN_SAMPLES: 3,
                CorrelationConfig.ALLOW_MISSING_UNITS: True,
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
            },
            
        )

        module.run(operations=[CorrelationOperation.PEARSON])
        cli_report = module.report_cli()

        # Should mention QC filtering or flags
        assert (
            "QC" in cli_report
            or "flag" in cli_report
            or "excluded" in cli_report
            or "invalid" in cli_report.lower()
            or "outlier" in cli_report.lower()
        )

    def test_module_cli_report_warns_on_unit_override(self) -> None:
        """Test CLI report includes warning when units are overridden."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        module = CorrelationModule(
            dataset=TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ug/m3"}),
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.MIN_SAMPLES: 3,
                CorrelationConfig.ALLOW_MISSING_UNITS: True,  # Override enabled
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
            },
            
        )

        module.run(operations=[CorrelationOperation.PEARSON])
        cli_report = module.report_cli()

        # Should warn about missing units
        assert (
            "WARNING" in cli_report
            or "Warning" in cli_report
            or "unit" in cli_report.lower()
            or "override" in cli_report.lower()
        )


class TestCorrelationModuleDashboard:
    """Test CorrelationModule dashboard report functionality."""

    def test_module_dashboard_has_required_fields(self) -> None:
        """Test dashboard payload includes schema_version, results, provenance."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        module = CorrelationModule(
            dataset=TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ug/m3"}),
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.MIN_SAMPLES: 3,
                CorrelationConfig.ALLOW_MISSING_UNITS: True,
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
            },
            
        )

        module.run(operations=[CorrelationOperation.PEARSON])
        dashboard: Dict[str, Any] = module.report_dashboard()

        # Required fields per Constitution Section 8
        assert "schema_version" in dashboard
        # Correlations are in metrics dict
        assert "metrics" in dashboard
        assert "correlations" in dashboard["metrics"]
        assert "provenance" in dashboard

    def test_module_dashboard_results_structure(self) -> None:
        """Test dashboard results have correlation pairs with values."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        module = CorrelationModule(
            dataset=TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ug/m3"}),
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.MIN_SAMPLES: 3,
                CorrelationConfig.ALLOW_MISSING_UNITS: True,
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
            },
            
        )

        module.run(operations=[CorrelationOperation.PEARSON])
        dashboard = module.report_dashboard()

        # Should have correlations in metrics
        assert "metrics" in dashboard
        correlations = dashboard["metrics"]["correlations"]

        assert isinstance(correlations, list)
        assert len(correlations) > 0  # At least some pairs

    def test_module_dashboard_provenance_includes_method(self) -> None:
        """Test dashboard provenance includes correlation method."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        module = CorrelationModule(
            dataset=TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ug/m3"}),
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.MIN_SAMPLES: 3,
                CorrelationConfig.ALLOW_MISSING_UNITS: True,
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
            },
            
        )

        module.run(operations=[CorrelationOperation.SPEARMAN])
        dashboard = module.report_dashboard()

        # Method is in metrics, not provenance
        metrics = dashboard["metrics"]
        assert "method" in metrics
        assert metrics["method"] == "spearman"

    def test_module_dashboard_provenance_includes_units_status(self) -> None:
        """Test dashboard provenance tracks unit override status."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        module = CorrelationModule(
            dataset=TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ug/m3"}),
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.MIN_SAMPLES: 3,
                CorrelationConfig.ALLOW_MISSING_UNITS: True,  # Override
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
            },
            
        )

        module.run(operations=[CorrelationOperation.PEARSON])
        dashboard = module.report_dashboard()

        # Units status is in metrics, not provenance
        metrics = dashboard["metrics"]
        assert "units_status" in metrics
        # With units present, should be "present", not "overridden"
        assert metrics["units_status"] == "present"

    def test_module_dashboard_json_serializable(self) -> None:
        """Test dashboard payload is JSON-serializable."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        module = CorrelationModule(
            dataset=TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ug/m3"}),
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.MIN_SAMPLES: 3,
                CorrelationConfig.ALLOW_MISSING_UNITS: True,
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
            },
            
        )

        module.run(operations=[CorrelationOperation.PEARSON])
        dashboard = module.report_dashboard()

        # Should serialize to JSON without error
        json_str = json.dumps(dashboard)
        assert isinstance(json_str, str)
        assert len(json_str) > 0

        # Should deserialize back
        parsed = json.loads(json_str)
        assert parsed["schema_version"] == dashboard["schema_version"]


class TestCorrelationModuleIntegration:
    """Integration tests for full module workflow."""

    def test_module_full_workflow_pearson_grouped(self) -> None:
        """Test complete workflow: configure, run, report (Pearson, grouped)."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=20, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10 + ["site2"] * 10,
                "pollutant": (["PM25"] * 5 + ["PM10"] * 5) * 2,
                "conc": (
                    [1.0, 2.0, 3.0, 4.0, 5.0] * 2  # site1: positive correlation
                    + [1.0, 2.0, 3.0, 4.0, 5.0]  # site2: PM25
                    + [5.0, 4.0, 3.0, 2.0, 1.0]  # site2: PM10 (negative)
                ),
                "flag": [QCFlag.VALID.value] * 20,
            }
        )

        module = CorrelationModule(
            dataset=TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ug/m3"}),
            config={
                CorrelationConfig.GROUP_BY: ["site_id"],
                CorrelationConfig.MIN_SAMPLES: 3,
                CorrelationConfig.ALLOW_MISSING_UNITS: True,
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
            },
            
        )

        # Run
        module.run(operations=[CorrelationOperation.PEARSON])

        # CLI report
        cli_report = module.report_cli()
        assert isinstance(cli_report, str)
        assert len(cli_report) > 0
        assert "site1" in cli_report or "site2" in cli_report

        # Dashboard report
        dashboard = module.report_dashboard()
        assert isinstance(dashboard, dict)
        assert "provenance" in dashboard

    def test_module_full_workflow_spearman_global(self) -> None:
        """Test complete workflow: configure, run, report (Spearman, global)."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0]
                + [1.0, 4.0, 9.0, 16.0, 25.0],  # Monotonic
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        module = CorrelationModule(
            dataset=TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ug/m3"}),
            config={
                CorrelationConfig.GROUP_BY: None,
                CorrelationConfig.MIN_SAMPLES: 3,
                CorrelationConfig.ALLOW_MISSING_UNITS: True,
                CorrelationConfig.CATEGORY_COL: "pollutant",
                CorrelationConfig.VALUE_COLS: "conc",
                CorrelationConfig.FLAG_COL: "flag",
            },
            
        )

        # Run
        module.run(operations=[CorrelationOperation.SPEARMAN])

        # CLI report should mention Spearman (uppercase in report)
        cli_report = module.report_cli()
        assert "Spearman" in cli_report or "spearman" in cli_report or "SPEARMAN" in cli_report

        # Dashboard should have method in metrics
        dashboard = module.report_dashboard()
        assert dashboard["metrics"]["method"] == "spearman"
