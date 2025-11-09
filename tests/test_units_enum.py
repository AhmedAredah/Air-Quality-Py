"""Tests for Unit Enum (Feature 002).

Constitution compliance:
- Section 10: Test coverage for core logic
- Validation: Unit.parse, enum members, error handling

Test scenarios (placeholder - skip markers):
1. Parse valid string tokens to Unit enum members
2. Parse existing Unit instance returns same instance
3. Parse invalid string raises UnitError with token in message
4. All enum members have expected string values
5. Enum is immutable (cannot add members at runtime)
"""

from __future__ import annotations

import pytest

from air_quality.exceptions import UnitError
from air_quality.units import Unit


class TestUnitEnum:
    """Test Unit Enum definition and parsing."""

    def test_unit_members_exist(self):
        """Verify all required Unit enum members exist."""
        # Expected members from spec: UG_M3, MG_M3, PPM, PPB
        assert hasattr(Unit, "UG_M3")
        assert hasattr(Unit, "MG_M3")
        assert hasattr(Unit, "PPM")
        assert hasattr(Unit, "PPB")

    def test_unit_member_values(self):
        """Verify enum members have correct string values."""
        assert Unit.UG_M3.symbol == "ug/m3"
        assert Unit.MG_M3.symbol == "mg/m3"
        assert Unit.PPM.symbol == "ppm"
        assert Unit.PPB.symbol == "ppb"

    def test_parse_valid_string(self):
        """Unit.parse converts valid string to enum member."""
        assert Unit.parse("ug/m3") == Unit.UG_M3
        assert Unit.parse("mg/m3") == Unit.MG_M3
        assert Unit.parse("ppm") == Unit.PPM
        assert Unit.parse("ppb") == Unit.PPB

    def test_parse_existing_unit(self):
        """Unit.parse returns same instance for Unit input."""
        assert Unit.parse(Unit.UG_M3) == Unit.UG_M3
        assert Unit.parse(Unit.PPM) is Unit.PPM

    def test_parse_invalid_string_raises_unit_error(self):
        """Unit.parse raises UnitError for unknown token."""
        with pytest.raises(UnitError) as exc_info:
            Unit.parse("invalid_unit")
        assert "invalid_unit" in str(exc_info.value)

    def test_parse_case_sensitive(self):
        """Unit.parse is case-sensitive (exact match required)."""
        with pytest.raises(UnitError):
            Unit.parse("UG/M3")  # uppercase not valid
        with pytest.raises(UnitError):
            Unit.parse("Ug/M3")  # mixed case not valid
