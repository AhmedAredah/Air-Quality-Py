"""
Placeholder tests for unit schema validation (US6).

Feature 002: Units & Time Primitives
User Story: US6 (Multi-Column Unit Metadata)
Phase: 8 (stub phase)

All tests marked with skip until implementation phase.
Tests validate contracts from specs/002-units-time/contracts/units_api.md.

Constitution compliance:
- Sec 3: Dataset metadata standards, fail-fast validation
- Sec 9: UnitError taxonomy, error messages with context
- Sec 15: Centralized unit validation, DRY principle
"""

import pytest
from air_quality.units import Unit
from air_quality.exceptions import UnitError


# ============================================================================
# US6: Multi-Column Unit Metadata Validation Tests
# ============================================================================


class TestValidateUnitsSchema:
    """Test unit schema normalization and validation (US6)."""

    def test_validate_units_schema_all_enum_values(self):
        """validate_units_schema with all Unit enum values returns unchanged."""
        # Given: Mapping with Unit enum values
        mapping = {
            "conc_ug": Unit.UG_M3,
            "conc_mg": Unit.MG_M3,
            "conc_ppm": Unit.PPM,
        }

        # When: Validating schema
        from air_quality.units import validate_units_schema

        result = validate_units_schema(mapping)

        # Then: Returns identical mapping
        assert result == mapping
        assert result["conc_ug"] is Unit.UG_M3
        assert result["conc_mg"] is Unit.MG_M3

    def test_validate_units_schema_all_string_values(self):
        """validate_units_schema normalizes all string values to Unit enums."""
        # Given: Mapping with string values
        mapping = {
            "pm25": "ug/m3",
            "no2": "ppb",
            "co": "ppm",
        }

        # When: Validating schema
        from air_quality.units import validate_units_schema

        result = validate_units_schema(mapping)

        # Then: All strings converted to Unit enums
        assert result["pm25"] == Unit.UG_M3
        assert result["no2"] == Unit.PPB
        assert result["co"] == Unit.PPM
        assert isinstance(result["pm25"], Unit)

    def test_validate_units_schema_mixed_types(self):
        """validate_units_schema handles mixed Unit and string values."""
        # Given: Mapping with mixed types
        mapping = {
            "col1": Unit.UG_M3,  # Already Unit
            "col2": "ppb",  # String to parse
            "col3": Unit.PPM,  # Already Unit
            "col4": "mg/m3",  # String to parse
        }

        # When: Validating schema
        from air_quality.units import validate_units_schema

        result = validate_units_schema(mapping)

        # Then: Unit values unchanged, strings normalized
        assert result["col1"] == Unit.UG_M3
        assert result["col2"] == Unit.PPB
        assert result["col3"] == Unit.PPM
        assert result["col4"] == Unit.MG_M3

    def test_validate_units_schema_invalid_unit_raises_with_column(self):
        """validate_units_schema raises UnitError with column name for invalid units."""
        # Given: Mapping with invalid unit string
        mapping = {
            "good_col": "ug/m3",
            "bad_col": "invalid_unit",
            "another_good": "ppb",
        }

        # When/Then: Raises UnitError mentioning offending column
        from air_quality.units import validate_units_schema

        with pytest.raises(UnitError, match="bad_col"):
            validate_units_schema(mapping)

    def test_validate_units_schema_empty_mapping(self):
        """validate_units_schema handles empty mapping."""
        # Given: Empty mapping
        mapping = {}

        # When: Validating empty schema
        from air_quality.units import validate_units_schema

        result = validate_units_schema(mapping)

        # Then: Returns empty dict
        assert result == {}
        assert isinstance(result, dict)

    def test_validate_units_schema_single_column(self):
        """validate_units_schema works with single column."""
        # Given: Single column mapping
        mapping = {"concentration": "ug/m3"}

        # When: Validating
        from air_quality.units import validate_units_schema

        result = validate_units_schema(mapping)

        # Then: Single entry normalized
        assert len(result) == 1
        assert result["concentration"] == Unit.UG_M3

    def test_validate_units_schema_preserves_column_names(self):
        """validate_units_schema preserves original column names as keys."""
        # Given: Mapping with various column name styles
        mapping = {
            "PM2.5_conc": "ug/m3",
            "NO2_ambient": "ppb",
            "column_123": "ppm",
        }

        # When: Validating
        from air_quality.units import validate_units_schema

        result = validate_units_schema(mapping)

        # Then: Column names unchanged
        assert "PM2.5_conc" in result
        assert "NO2_ambient" in result
        assert "column_123" in result

    def test_validate_units_schema_case_sensitivity_follows_parse(self):
        """validate_units_schema case handling follows Unit.parse() behavior."""
        # Given: String values with different cases
        # (Assuming Unit.parse() is case-sensitive based on enum values)
        mapping = {
            "col1": "ug/m3",  # Lowercase (standard)
            # "col2": "UG/M3",  # Uppercase - may fail if parse is case-sensitive
        }

        # When: Validating
        from air_quality.units import validate_units_schema

        result = validate_units_schema(mapping)

        # Then: Standard case works
        assert result["col1"] == Unit.UG_M3

    def test_validate_units_schema_multiple_invalid_reports_first(self):
        """validate_units_schema reports first invalid unit encountered."""
        # Given: Multiple invalid units
        mapping = {
            "col1": "ug/m3",
            "col2": "bad_unit_1",
            "col3": "bad_unit_2",
        }

        # When/Then: Raises UnitError (may report first invalid)
        from air_quality.units import validate_units_schema

        with pytest.raises(UnitError):
            validate_units_schema(mapping)

    def test_validate_units_schema_returns_new_dict(self):
        """validate_units_schema returns new dict (does not mutate input)."""
        # Given: Original mapping
        original = {"col": "ug/m3"}

        # When: Validating
        from air_quality.units import validate_units_schema

        result = validate_units_schema(original)

        # Then: New dict returned, original unchanged
        assert result is not original
        assert original["col"] == "ug/m3"  # Still string
        assert isinstance(result["col"], Unit)  # Normalized to Unit

    def test_validate_units_schema_with_all_supported_units(self):
        """validate_units_schema handles all supported unit types."""
        # Given: Mapping with all defined units
        mapping = {
            "ug_col": Unit.UG_M3,
            "mg_col": Unit.MG_M3,
            "ppm_col": Unit.PPM,
            "ppb_col": Unit.PPB,
        }

        # When: Validating
        from air_quality.units import validate_units_schema

        result = validate_units_schema(mapping)

        # Then: All units present
        assert len(result) == 4
        assert result["ug_col"] == Unit.UG_M3
        assert result["mg_col"] == Unit.MG_M3
        assert result["ppm_col"] == Unit.PPM
        assert result["ppb_col"] == Unit.PPB


class TestValidateUnitsSchemaIntegration:
    """Integration scenarios for unit schema validation (US6)."""

    def test_validate_units_schema_dataset_construction_scenario(self):
        """Simulate dataset construction with unit metadata validation."""
        # Given: Typical dataset metadata scenario
        user_provided_units = {
            "PM2.5": "ug/m3",
            "NO2": "ppb",
            "O3": "ppm",
        }

        # When: Validating as part of dataset construction
        from air_quality.units import validate_units_schema

        normalized = validate_units_schema(user_provided_units)

        # Then: Ready for metadata storage
        assert all(isinstance(v, Unit) for v in normalized.values())
        assert normalized["PM2.5"] == Unit.UG_M3

    def test_validate_units_schema_error_context_for_debugging(self):
        """UnitError message provides helpful context for debugging."""
        # Given: Invalid unit that needs user correction
        mapping = {
            "temperature": "celsius",  # Not supported (out of scope)
            "pressure": "pa",  # Not supported
        }

        # When/Then: Error message includes column name
        from air_quality.units import validate_units_schema

        with pytest.raises(UnitError) as exc_info:
            validate_units_schema(mapping)

        # Error should mention column name for user to fix
        assert "temperature" in str(exc_info.value) or "pressure" in str(exc_info.value)

    def test_validate_units_schema_typical_air_quality_columns(self):
        """Validate typical air quality dataset column units."""
        # Given: Common air quality pollutant columns
        mapping = {
            "PM2.5_hourly": "ug/m3",
            "PM10_hourly": "ug/m3",
            "NO2_hourly": "ppb",
            "O3_8hr": "ppm",
            "CO_hourly": "ppm",
            "SO2_hourly": "ppb",
        }

        # When: Validating
        from air_quality.units import validate_units_schema

        result = validate_units_schema(mapping)

        # Then: All normalized correctly
        assert result["PM2.5_hourly"] == Unit.UG_M3
        assert result["PM10_hourly"] == Unit.UG_M3
        assert result["NO2_hourly"] == Unit.PPB
        assert result["O3_8hr"] == Unit.PPM
        assert result["CO_hourly"] == Unit.PPM
        assert result["SO2_hourly"] == Unit.PPB

    def test_validate_units_schema_fail_fast_behavior(self):
        """validate_units_schema fails fast on first error (Constitution Sec 3)."""
        # Given: Mix of valid and invalid
        mapping = {
            "valid1": "ug/m3",
            "invalid": "not_a_unit",
            "valid2": "ppb",
        }

        # When/Then: Fails immediately on invalid (does not process all)
        from air_quality.units import validate_units_schema

        with pytest.raises(UnitError):
            validate_units_schema(mapping)

        # Constitution requires fail-fast, not silent ignoring
