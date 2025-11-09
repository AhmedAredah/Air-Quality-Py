"""
Integration tests for unit metadata in TimeSeriesDataset (Phase 8).

Feature 002: Units & Time Primitives
Phase: 8 (Dataset Integration)

Tests validate integration of validate_units_schema() with TimeSeriesDataset.

Constitution compliance:
- Sec 3: Dataset metadata standards, unit normalization
- Sec 9: UnitError taxonomy with column context
- Sec 15: Centralized unit validation, DRY principle
"""

import pytest
import pandas as pd
from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.units import Unit
from air_quality.exceptions import UnitError


# ============================================================================
# Dataset Construction with Unit Metadata Tests
# ============================================================================


class TestDatasetUnitsIntegration:
    """Test unit metadata integration with TimeSeriesDataset."""

    def test_dataset_accepts_column_units_as_dict(self):
        """TimeSeriesDataset accepts column_units parameter."""
        # Given: DataFrame with concentration data
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="h"),
                "site_id": ["A"] * 3,
                "pollutant": ["PM2.5"] * 3,
                "conc": [10.0, 12.0, 14.0],
            }
        )

        # When: Creating dataset with unit metadata
        dataset = TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ug/m3"})

        # Then: Dataset created successfully
        assert dataset.n_rows == 3
        assert dataset.column_units is not None

    def test_dataset_normalizes_string_units_to_enum(self):
        """TimeSeriesDataset normalizes string units to Unit enums."""
        # Given: DataFrame and string unit metadata
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="h"),
                "site_id": ["A"] * 3,
                "pollutant": ["NO2"] * 3,
                "conc": [20.0, 22.0, 24.0],
            }
        )

        # When: Creating dataset with string unit
        dataset = TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ppb"})

        # Then: String normalized to Unit enum
        assert dataset.column_units["conc"] == Unit.PPB
        assert isinstance(dataset.column_units["conc"], Unit)

    def test_dataset_accepts_mixed_unit_types(self):
        """TimeSeriesDataset accepts mixed Unit enum and string values."""
        # Given: DataFrame with multiple columns
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="h"),
                "site_id": ["A"] * 3,
                "pollutant": ["PM2.5"] * 3,
                "conc": [10.0, 12.0, 14.0],
                "unc": [1.0, 1.2, 1.4],
            }
        )

        # When: Creating dataset with mixed types (Unit + string)
        dataset = TimeSeriesDataset.from_dataframe(
            df,
            column_units={
                "conc": Unit.UG_M3,  # Already Unit enum
                "unc": "ug/m3",  # String to be normalized
            },
        )

        # Then: Both normalized to Unit enums
        assert dataset.column_units["conc"] == Unit.UG_M3
        assert dataset.column_units["unc"] == Unit.UG_M3
        assert all(isinstance(v, Unit) for v in dataset.column_units.values())

    def test_dataset_invalid_unit_raises_unit_error_with_column(self):
        """TimeSeriesDataset raises UnitError with column name for invalid units."""
        # Given: DataFrame and invalid unit string
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="h"),
                "site_id": ["A"] * 3,
                "pollutant": ["PM2.5"] * 3,
                "conc": [10.0, 12.0, 14.0],
            }
        )

        # When/Then: Raises UnitError mentioning column name
        with pytest.raises(UnitError, match="conc"):
            TimeSeriesDataset.from_dataframe(df, column_units={"conc": "invalid_unit"})

    def test_dataset_column_units_property_returns_normalized_mapping(self):
        """column_units property returns normalized Unit mapping."""
        # Given: Dataset with unit metadata
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="h"),
                "site_id": ["A"] * 3,
                "pollutant": ["O3"] * 3,
                "conc": [50.0, 52.0, 54.0],
            }
        )
        dataset = TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ppm"})

        # When: Accessing column_units property
        units = dataset.column_units

        # Then: Returns dict with Unit values
        assert isinstance(units, dict)
        assert units["conc"] == Unit.PPM

    def test_dataset_column_units_none_when_not_provided(self):
        """column_units property returns None when not provided."""
        # Given: Dataset without unit metadata
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="h"),
                "site_id": ["A"] * 3,
                "pollutant": ["PM2.5"] * 3,
                "conc": [10.0, 12.0, 14.0],
            }
        )

        # When: Creating dataset without column_units
        dataset = TimeSeriesDataset.from_dataframe(df)

        # Then: column_units is None
        assert dataset.column_units is None

    def test_dataset_empty_column_units_dict(self):
        """TimeSeriesDataset handles empty column_units dict."""
        # Given: DataFrame and empty unit dict
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="h"),
                "site_id": ["A"] * 3,
                "pollutant": ["PM2.5"] * 3,
                "conc": [10.0, 12.0, 14.0],
            }
        )

        # When: Creating dataset with empty dict
        dataset = TimeSeriesDataset.from_dataframe(df, column_units={})

        # Then: column_units is empty dict
        assert dataset.column_units == {}
        assert isinstance(dataset.column_units, dict)

    def test_dataset_multiple_columns_with_units(self):
        """TimeSeriesDataset handles multiple columns with different units."""
        # Given: DataFrame with multiple pollutants
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="h"),
                "site_id": ["A"] * 3,
                "pollutant": ["PM2.5"] * 3,
                "pm25_conc": [10.0, 12.0, 14.0],
                "no2_conc": [20.0, 22.0, 24.0],
                "o3_conc": [50.0, 52.0, 54.0],
            }
        )

        # When: Creating dataset with multiple unit specs
        dataset = TimeSeriesDataset.from_dataframe(
            df,
            column_units={
                "pm25_conc": "ug/m3",
                "no2_conc": "ppb",
                "o3_conc": "ppm",
            },
        )

        # Then: All units normalized correctly
        assert dataset.column_units["pm25_conc"] == Unit.UG_M3
        assert dataset.column_units["no2_conc"] == Unit.PPB
        assert dataset.column_units["o3_conc"] == Unit.PPM

    def test_dataset_from_arrow_accepts_column_units(self):
        """TimeSeriesDataset.from_arrow accepts column_units parameter."""
        # Given: PyArrow table
        import pyarrow as pa

        table = pa.table(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="h"),
                "site_id": ["A"] * 3,
                "pollutant": ["PM2.5"] * 3,
                "conc": [10.0, 12.0, 14.0],
            }
        )

        # When: Creating dataset from Arrow with units
        dataset = TimeSeriesDataset.from_arrow(table, column_units={"conc": "ug/m3"})

        # Then: Units processed correctly
        assert dataset.column_units["conc"] == Unit.UG_M3


class TestDatasetUnitsImmutability:
    """Test immutability of unit metadata."""

    def test_column_units_property_does_not_mutate_metadata(self):
        """Accessing column_units does not mutate underlying metadata."""
        # Given: Dataset with unit metadata
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="h"),
                "site_id": ["A"] * 3,
                "pollutant": ["PM2.5"] * 3,
                "conc": [10.0, 12.0, 14.0],
            }
        )
        dataset = TimeSeriesDataset.from_dataframe(df, column_units={"conc": "ug/m3"})

        # When: Accessing property multiple times
        units1 = dataset.column_units
        units2 = dataset.column_units

        # Then: Returns same underlying object (no mutation)
        assert units1 is units2
        assert units1 == units2


class TestDatasetUnitsErrorHandling:
    """Test error handling for unit metadata."""

    def test_invalid_unit_error_message_includes_column_name(self):
        """Error message includes column name for debugging."""
        # Given: DataFrame with invalid unit
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="h"),
                "site_id": ["A"] * 3,
                "pollutant": ["PM2.5"] * 3,
                "temperature": [20.0, 21.0, 22.0],  # Invalid unit scenario
            }
        )

        # When/Then: Error mentions column name
        with pytest.raises(UnitError) as exc_info:
            TimeSeriesDataset.from_dataframe(
                df, column_units={"temperature": "celsius"}  # Not supported
            )

        error_msg = str(exc_info.value)
        assert "temperature" in error_msg

    def test_multiple_invalid_columns_reports_first(self):
        """Multiple invalid units: reports first encountered."""
        # Given: DataFrame with multiple invalid units
        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2024-01-01", periods=3, freq="h"),
                "site_id": ["A"] * 3,
                "pollutant": ["PM2.5"] * 3,
                "col1": [1.0, 2.0, 3.0],
                "col2": [4.0, 5.0, 6.0],
            }
        )

        # When/Then: Raises UnitError (may report first invalid)
        with pytest.raises(UnitError):
            TimeSeriesDataset.from_dataframe(
                df,
                column_units={
                    "col1": "bad_unit_1",
                    "col2": "bad_unit_2",
                },
            )
