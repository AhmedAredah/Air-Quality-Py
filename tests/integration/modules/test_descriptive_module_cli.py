"""Integration tests for DescriptiveStatsModule CLI and dashboard reporting.

Test ID: T022
Module: air_quality.modules.statistics.descriptive
Focus: Module lifecycle, CLI report, dashboard payload
"""

import pandas as pd
import pytest

from air_quality.modules.statistics.descriptive import (
    DescriptiveStatsModule,
    DescriptiveStatsConfig,
)
from air_quality.qc_flags import QCFlag


class TestDescriptiveStatsModuleIntegration:
    """Integration tests for DescriptiveStatsModule."""

    @pytest.fixture
    def sample_dataframe(self) -> pd.DataFrame:
        """Create a sample dataframe for testing."""
        return pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=100, freq="h"),
                "site_id": ["Site_A"] * 50 + ["Site_B"] * 50,
                "pollutant": ["PM25"] * 100,
                "conc": list(range(1, 101)),
                "flag": [QCFlag.VALID.value] * 90 + [QCFlag.INVALID.value] * 10,
            }
        )

    def test_module_from_dataframe(self, sample_dataframe):
        """Test creating module from dataframe."""
        module = DescriptiveStatsModule.from_dataframe(
            sample_dataframe,
            config={},
        )

        assert module is not None
        assert module.dataset is not None
        assert module.dataset.n_rows == 100

    def test_module_run_populates_results(self, sample_dataframe):
        """Test that run() populates results."""
        module = DescriptiveStatsModule.from_dataframe(
            sample_dataframe,
            config={},
        )

        result = module.run()

        # Should have populated results
        assert module.results is not None
        assert len(module.results) > 0

    def test_module_run_returns_self(self, sample_dataframe):
        """Test that run() returns self for method chaining."""
        module = DescriptiveStatsModule.from_dataframe(
            sample_dataframe,
            config={},
        )

        result = module.run()

        # Result should be the module itself (for method chaining)
        assert result is module
        # But module.results should be a dict with enum keys
        assert isinstance(module.results, dict)

    def test_report_dashboard_structure(self, sample_dataframe):
        """Test dashboard report structure."""
        module = DescriptiveStatsModule.from_dataframe(
            sample_dataframe,
            config={},
        )
        module.run()

        dashboard = module.report_dashboard()

        # Should have required fields per Constitution Section 8
        assert "module" in dashboard
        assert "domain" in dashboard
        assert "schema_version" in dashboard
        assert "provenance" in dashboard
        assert "metrics" in dashboard

    def test_report_dashboard_metrics_content(self, sample_dataframe):
        """Test that dashboard metrics contain statistics."""
        module = DescriptiveStatsModule.from_dataframe(
            sample_dataframe,
            config={},
        )
        module.run()

        dashboard = module.report_dashboard()
        metrics = dashboard["metrics"]

        # Should have statistics results
        assert "statistics" in metrics or len(metrics) > 0

    def test_report_cli_returns_string(self, sample_dataframe):
        """Test that CLI report returns a string."""
        module = DescriptiveStatsModule.from_dataframe(
            sample_dataframe,
            config={},
        )
        module.run()

        cli_report = module.report_cli()

        assert isinstance(cli_report, str)
        assert len(cli_report) > 0

    def test_report_cli_contains_summary(self, sample_dataframe):
        """Test that CLI report contains human-readable summary."""
        module = DescriptiveStatsModule.from_dataframe(
            sample_dataframe,
            config={},
        )
        module.run()

        cli_report = module.report_cli()

        # Should contain descriptive information
        assert "Descriptive" in cli_report or "Statistics" in cli_report
        # Should contain count information
        assert "n_total" in cli_report.lower() or "total" in cli_report.lower()

    def test_module_with_grouping_config(self, sample_dataframe):
        """Test module with group_by configuration."""
        module = DescriptiveStatsModule.from_dataframe(
            sample_dataframe,
            config={DescriptiveStatsConfig.GROUP_BY: ["site_id"]},
        )
        module.run()

        # Should have results for grouped data
        assert module.results is not None

    def test_module_with_custom_quantiles(self, sample_dataframe):
        """Test module with custom quantile configuration."""
        module = DescriptiveStatsModule.from_dataframe(
            sample_dataframe,
            config={DescriptiveStatsConfig.QUANTILES: (0.1, 0.5, 0.9)},
        )
        module.run()

        # Should have results
        assert module.results is not None

    def test_provenance_attached_after_run(self, sample_dataframe):
        """Test that provenance is attached after run()."""
        module = DescriptiveStatsModule.from_dataframe(
            sample_dataframe,
            config={},
        )

        # Before run
        assert module.provenance is None

        # After run
        module.run()
        assert module.provenance is not None

    def test_provenance_includes_config_hash(self, sample_dataframe):
        """Test that provenance includes config hash."""
        module = DescriptiveStatsModule.from_dataframe(
            sample_dataframe,
            config={DescriptiveStatsConfig.GROUP_BY: ["site_id"]},
        )
        module.run()

        dashboard = module.report_dashboard()
        provenance = dashboard["provenance"]

        # Should have config_hash per Constitution Section 15
        assert "config_hash" in provenance

    def test_provenance_includes_timestamp(self, sample_dataframe):
        """Test that provenance includes run timestamp."""
        module = DescriptiveStatsModule.from_dataframe(
            sample_dataframe,
            config={},
        )
        module.run()

        dashboard = module.report_dashboard()
        provenance = dashboard["provenance"]

        # Should have run_timestamp
        assert "run_timestamp" in provenance

    def test_multi_pollutant_dataset(self):
        """Test module with multi-pollutant dataset."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=100, freq="h"),
                "site_id": ["Site_A"] * 100,
                "pollutant": ["PM25"] * 50 + ["NO2"] * 50,
                "conc": list(range(1, 101)),
                "flag": [QCFlag.VALID.value] * 100,
            }
        )

        module = DescriptiveStatsModule.from_dataframe(
            df,
            config={},
        )
        module.run()

        # Should handle both pollutants
        assert module.results is not None

    def test_multi_site_multi_pollutant(self):
        """Test module with multi-site and multi-pollutant dataset."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=200, freq="h"),
                "site_id": ["Site_A"] * 100 + ["Site_B"] * 100,
                "pollutant": (["PM25"] * 50 + ["NO2"] * 50) * 2,
                "conc": list(range(1, 201)),
                "flag": [QCFlag.VALID.value] * 200,
            }
        )

        module = DescriptiveStatsModule.from_dataframe(
            df,
            config={DescriptiveStatsConfig.GROUP_BY: ["site_id"]},
        )
        module.run()

        # Should handle all combinations
        assert module.results is not None

    def test_cli_report_shows_qc_summary(self, sample_dataframe):
        """Test that CLI report shows QC filtering summary."""
        module = DescriptiveStatsModule.from_dataframe(
            sample_dataframe,
            config={},
        )
        module.run()

        cli_report = module.report_cli()

        # Should mention valid/invalid counts or QC filtering
        # (90 valid + 10 invalid in fixture)
        report_lower = cli_report.lower()
        assert any(word in report_lower for word in ["valid", "invalid", "qc", "flag"])

    def test_empty_dataset_after_filtering(self):
        """Test handling of dataset with all data filtered out."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=10, freq="h"),
                "site_id": ["Site_A"] * 10,
                "pollutant": ["PM25"] * 10,
                "conc": list(range(10)),
                "flag": [QCFlag.INVALID.value] * 10,
            }
        )

        module = DescriptiveStatsModule.from_dataframe(
            df,
            config={},
        )
        module.run()

        # Should still complete (results with NaN values)
        assert module.results is not None

        cli_report = module.report_cli()
        assert len(cli_report) > 0

    def test_minimal_dataset(self):
        """Test with minimal valid dataset (1 row)."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-01-01", periods=1, freq="h"),
                "site_id": ["Site_A"],
                "pollutant": ["PM25"],
                "conc": [42.0],
                "flag": [QCFlag.VALID.value],
            }
        )

        module = DescriptiveStatsModule.from_dataframe(
            df,
            config={},
        )
        module.run()

        # Should handle single data point
        assert module.results is not None
