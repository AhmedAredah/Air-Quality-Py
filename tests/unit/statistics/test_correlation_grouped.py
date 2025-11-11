"""Unit tests for grouped correlation analysis.

Tests correlation computation with grouping by site_id and pair ordering.

Constitution References
-----------------------
- Section 5: QC flag filtering within groups
- Section 11: Grouped vectorized operations
- Section 15: Provenance per group
"""

from __future__ import annotations

import pandas as pd
import polars as pl
import pytest

from air_quality.analysis.correlation import compute_pairwise
from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.qc_flags import QCFlag


class TestGroupedCorrelation:
    """Test grouped correlation functionality."""

    def test_correlation_grouped_by_site(self) -> None:
        """Test correlation computed separately per site_id."""
        # Site1: Perfect positive correlation
        # Site2: Perfect negative correlation
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=20, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10 + ["site2"] * 10,
                "pollutant": (["PM25"] * 5 + ["PM10"] * 5) * 2,
                "conc": (
                    [1.0, 2.0, 3.0, 4.0, 5.0] * 2  # site1: same pattern
                    + [1.0, 2.0, 3.0, 4.0, 5.0]  # site2: PM25
                    + [5.0, 4.0, 3.0, 2.0, 1.0]  # site2: PM10 (reverse)
                ),
                "flag": [QCFlag.VALID.value] * 20,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=["site_id"],
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have 6 rows: 3 pairs x 2 sites
        assert len(result) == 6

        # Site1: PM10-PM25 perfect positive
        site1_cross = result[
            (result["site_id"] == "site1")
            & (result["var_x"] == "PM10")
            & (result["var_y"] == "PM25")
        ].iloc[0]
        assert site1_cross["correlation"] == pytest.approx(1.0, abs=1e-9)
        assert site1_cross["n"] == 5

        # Site2: PM10-PM25 perfect negative
        site2_cross = result[
            (result["site_id"] == "site2")
            & (result["var_x"] == "PM10")
            & (result["var_y"] == "PM25")
        ].iloc[0]
        assert site2_cross["correlation"] == pytest.approx(-1.0, abs=1e-9)
        assert site2_cross["n"] == 5

    def test_correlation_grouped_by_multiple_keys(self) -> None:
        """Test correlation with multiple grouping keys."""
        # Each (site_id, state) group should have both pollutants
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=40, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10
                + ["site1"] * 10
                + ["site2"] * 10
                + ["site2"] * 10,
                "state": ["CA"] * 10 + ["TX"] * 10 + ["CA"] * 10 + ["TX"] * 10,
                "pollutant": (["PM25"] * 5 + ["PM10"] * 5)
                * 4,  # Both pollutants in each group
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 8,
                "flag": [QCFlag.VALID.value] * 40,
            }
        )

        # Add state to dataset metadata
        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=["site_id", "state"],
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have 12 rows: 3 pairs x 4 groups (site1-CA, site1-TX, site2-CA, site2-TX)
        assert len(result) == 12

        # Check distinct group combinations
        groups = result[["site_id", "state"]].drop_duplicates()
        assert len(groups) == 4

    def test_grouped_correlation_maintains_pair_ordering(self) -> None:
        """Test pair ordering (var_x <= var_y) is maintained within each group."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=30, freq="h", tz="UTC"),
                "site_id": ["site1"] * 15 + ["site2"] * 15,
                "pollutant": (["CO"] * 5 + ["NO2"] * 5 + ["O3"] * 5) * 2,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 6,
                "flag": [QCFlag.VALID.value] * 30,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=["site_id"],
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Should have 12 rows: 6 pairs x 2 sites
        assert len(result) == 12

        # Check ordering within each group
        for site in ["site1", "site2"]:
            site_rows = result[result["site_id"] == site]
            for _, row in site_rows.iterrows():
                assert (
                    row["var_x"] <= row["var_y"]
                ), f"Pair ordering violated in {site}: {row['var_x']} > {row['var_y']}"

    def test_grouped_correlation_includes_diagonal_per_group(self) -> None:
        """Test diagonal (self-correlation) is included for each group."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=20, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10 + ["site2"] * 10,
                "pollutant": (["PM25"] * 5 + ["PM10"] * 5) * 2,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 4,
                "flag": [QCFlag.VALID.value] * 20,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=["site_id"],
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Check diagonal for site1
        site1_pm10_pm10 = result[
            (result["site_id"] == "site1")
            & (result["var_x"] == "PM10")
            & (result["var_y"] == "PM10")
        ]
        assert len(site1_pm10_pm10) == 1
        assert site1_pm10_pm10.iloc[0]["correlation"] == pytest.approx(1.0, abs=1e-9)

        site1_pm25_pm25 = result[
            (result["site_id"] == "site1")
            & (result["var_x"] == "PM25")
            & (result["var_y"] == "PM25")
        ]
        assert len(site1_pm25_pm25) == 1
        assert site1_pm25_pm25.iloc[0]["correlation"] == pytest.approx(1.0, abs=1e-9)

        # Check diagonal for site2
        site2_pm10_pm10 = result[
            (result["site_id"] == "site2")
            & (result["var_x"] == "PM10")
            & (result["var_y"] == "PM10")
        ]
        assert len(site2_pm10_pm10) == 1
        assert site2_pm10_pm10.iloc[0]["correlation"] == pytest.approx(1.0, abs=1e-9)

    def test_grouped_correlation_respects_qc_flags_per_group(self) -> None:
        """Test QC flag filtering is applied within each group independently."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=20, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10 + ["site2"] * 10,
                "pollutant": (["PM25"] * 5 + ["PM10"] * 5) * 2,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 4,
                "flag": (
                    [QCFlag.VALID.value] * 3
                    + [QCFlag.INVALID.value] * 2  # site1: PM25 has 2 invalid
                    + [QCFlag.VALID.value] * 5  # site1: PM10 all valid
                    + [QCFlag.VALID.value] * 5  # site2: PM25 all valid
                    + [QCFlag.VALID.value] * 3
                    + [QCFlag.OUTLIER.value] * 2  # site2: PM10 has 2 outliers
                ),
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=["site_id"],
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Site1: PM25 should have 3 valid observations
        site1_pm25 = result[
            (result["site_id"] == "site1")
            & (result["var_x"] == "PM25")
            & (result["var_y"] == "PM25")
        ].iloc[0]
        assert site1_pm25["n"] == 3

        # Site1: PM10 should have 5 valid observations
        site1_pm10 = result[
            (result["site_id"] == "site1")
            & (result["var_x"] == "PM10")
            & (result["var_y"] == "PM10")
        ].iloc[0]
        assert site1_pm10["n"] == 5

        # Site2: PM25 should have 5 valid observations
        site2_pm25 = result[
            (result["site_id"] == "site2")
            & (result["var_x"] == "PM25")
            & (result["var_y"] == "PM25")
        ].iloc[0]
        assert site2_pm25["n"] == 5

        # Site2: PM10 should have 3 valid observations
        site2_pm10 = result[
            (result["site_id"] == "site2")
            & (result["var_x"] == "PM10")
            & (result["var_y"] == "PM10")
        ].iloc[0]
        assert site2_pm10["n"] == 3

    def test_grouped_correlation_with_unequal_group_sizes(self) -> None:
        """Test correlation handles groups with different sample sizes."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=22, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10 + ["site2"] * 12,  # Unequal sizes
                "pollutant": (["PM25"] * 5 + ["PM10"] * 5)
                + (["PM25"] * 6 + ["PM10"] * 6),
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2
                + [1.0, 2.0, 3.0, 4.0, 5.0, 6.0] * 2,
                "flag": [QCFlag.VALID.value] * 22,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=["site_id"],
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Site1 should have n=5
        site1_cross = result[
            (result["site_id"] == "site1")
            & (result["var_x"] == "PM10")
            & (result["var_y"] == "PM25")
        ].iloc[0]
        assert site1_cross["n"] == 5

        # Site2 should have n=6
        site2_cross = result[
            (result["site_id"] == "site2")
            & (result["var_x"] == "PM10")
            & (result["var_y"] == "PM25")
        ].iloc[0]
        assert site2_cross["n"] == 6

    def test_grouped_correlation_with_missing_pollutant_in_group(self) -> None:
        """Test correlation when some groups have missing pollutants."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=20, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10 + ["site2"] * 10,
                "pollutant": (
                    ["PM25"] * 5
                    + ["PM10"] * 5
                    + ["PM25"] * 10  # site2: only PM25, no PM10
                ),
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 4,
                "flag": [QCFlag.VALID.value] * 20,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        result = compute_pairwise(
            dataset=dataset,
            group_by=["site_id"],
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result, pl.DataFrame):
            result = result.to_pandas()

        # Site1 should have 3 pairs (PM10-PM10, PM10-PM25, PM25-PM25)
        site1_rows = result[result["site_id"] == "site1"]
        assert len(site1_rows) == 3

        # Site2 should have only 1 pair (PM25-PM25)
        site2_rows = result[result["site_id"] == "site2"]
        assert len(site2_rows) == 1
        assert site2_rows.iloc[0]["var_x"] == "PM25"
        assert site2_rows.iloc[0]["var_y"] == "PM25"

    def test_global_correlation_equivalent_to_single_group(self) -> None:
        """Test global correlation (group_by=None) matches single-group result."""
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
                "site_id": ["site1"] * 10,
                "pollutant": ["PM25"] * 5 + ["PM10"] * 5,
                "conc": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
                "flag": [QCFlag.VALID.value] * 10,
            }
        )

        dataset = TimeSeriesDataset.from_dataframe(df)

        # Global correlation
        result_global = compute_pairwise(
            dataset=dataset,
            group_by=None,
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        # Grouped by site
        result_grouped = compute_pairwise(
            dataset=dataset,
            group_by=["site_id"],
            correlation_type="pearson",
            category_col="pollutant",
            value_cols="conc",
            flag_col="flag",
            allow_missing_units=True,  # Focus on correlation logic
        )

        if isinstance(result_global, pl.DataFrame):
            result_global = result_global.to_pandas()
        if isinstance(result_grouped, pl.DataFrame):
            result_grouped = result_grouped.to_pandas()

        # Same number of pairs (3)
        assert len(result_global) == 3
        assert len(result_grouped) == 3

        # Grouped result has site_id column
        assert "site_id" in result_grouped.columns
        assert "site_id" not in result_global.columns

        # Correlation values should match
        for _, global_row in result_global.iterrows():
            grouped_row = result_grouped[
                (result_grouped["var_x"] == global_row["var_x"])
                & (result_grouped["var_y"] == global_row["var_y"])
            ].iloc[0]
            assert grouped_row["correlation"] == pytest.approx(
                global_row["correlation"], abs=1e-9
            )
            assert grouped_row["n"] == global_row["n"]
