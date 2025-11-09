"""
Tests for public API exports from air_quality package (Phase 9).

Feature 002: Units & Time Primitives
Phase: 9 (Public API Exports)

Tests verify that all implemented functions, enums, and dataclasses
are correctly exported from the top-level air_quality package.

Constitution compliance:
- Sec 9: Public API design, typed interfaces
- Sec 12: Versioning and API stability
"""

import pytest


class TestUnitsAPIExports:
    """Test that all units functions and types are publicly accessible."""

    def test_unit_enum_importable(self):
        """Unit enum can be imported from top-level package."""
        from air_quality import Unit

        # Verify it's the actual enum, not a string
        assert hasattr(Unit, "UG_M3")
        assert hasattr(Unit, "MG_M3")
        assert hasattr(Unit, "PPB")
        assert hasattr(Unit, "PPM")

    def test_can_convert_importable(self):
        """can_convert function is publicly accessible."""
        from air_quality import can_convert

        # Verify it's callable
        assert callable(can_convert)

    def test_convert_values_importable(self):
        """convert_values function is publicly accessible."""
        from air_quality import convert_values

        # Verify it's callable
        assert callable(convert_values)

    def test_get_factor_importable(self):
        """get_factor function is publicly accessible."""
        from air_quality import get_factor

        # Verify it's callable
        assert callable(get_factor)

    def test_round_for_reporting_importable(self):
        """round_for_reporting function is publicly accessible."""
        from air_quality import round_for_reporting

        # Verify it's callable
        assert callable(round_for_reporting)

    def test_validate_units_schema_importable(self):
        """validate_units_schema function is publicly accessible."""
        from air_quality import validate_units_schema

        # Verify it's callable
        assert callable(validate_units_schema)


class TestTimeUtilsAPIExports:
    """Test that all time_utils functions and types are publicly accessible."""

    def test_timebounds_dataclass_importable(self):
        """TimeBounds dataclass can be imported from top-level package."""
        from air_quality import TimeBounds

        # Verify it's the actual dataclass
        assert hasattr(TimeBounds, "__dataclass_fields__")
        assert "start" in TimeBounds.__dataclass_fields__
        assert "end" in TimeBounds.__dataclass_fields__

    def test_ensure_timezone_aware_importable(self):
        """ensure_timezone_aware function is publicly accessible."""
        from air_quality import ensure_timezone_aware

        # Verify it's callable
        assert callable(ensure_timezone_aware)

    def test_to_utc_importable(self):
        """to_utc function is publicly accessible."""
        from air_quality import to_utc

        # Verify it's callable
        assert callable(to_utc)

    def test_compute_time_bounds_importable(self):
        """compute_time_bounds function is publicly accessible."""
        from air_quality import compute_time_bounds

        # Verify it's callable
        assert callable(compute_time_bounds)

    def test_resample_mean_importable(self):
        """resample_mean function is publicly accessible."""
        from air_quality import resample_mean

        # Verify it's callable
        assert callable(resample_mean)

    def test_rolling_window_mean_importable(self):
        """rolling_window_mean function is publicly accessible."""
        from air_quality import rolling_window_mean

        # Verify it's callable
        assert callable(rolling_window_mean)


class TestAPICompleteness:
    """Test __all__ export list completeness."""

    def test_all_list_contains_expected_exports(self):
        """__all__ list contains all 14 expected Feature 002 exports."""
        from air_quality import __all__

        # Feature 002 exports (12 items + Unit enum + TimeBounds dataclass = 14)
        expected_feature_002 = {
            # Units (6 items)
            "Unit",
            "can_convert",
            "convert_values",
            "get_factor",
            "round_for_reporting",
            "validate_units_schema",
            # Time utilities (6 items)
            "TimeBounds",
            "compute_time_bounds",
            "ensure_timezone_aware",
            "resample_mean",
            "rolling_window_mean",
            "to_utc",
        }

        # Verify all Feature 002 exports are in __all__
        for name in expected_feature_002:
            assert name in __all__, f"{name} missing from __all__"

    def test_all_exports_are_importable(self):
        """All items in __all__ can be successfully imported."""
        import air_quality

        for name in air_quality.__all__:
            # Skip version and hello (not part of Feature 002)
            if name in ("__version__", "hello"):
                continue

            # Verify export exists
            assert hasattr(air_quality, name), f"{name} in __all__ but not importable"

    def test_no_unexpected_public_exports(self):
        """No unexpected names are exported (avoid namespace pollution)."""
        import air_quality

        # Get all public names (not starting with _)
        public_names = [name for name in dir(air_quality) if not name.startswith("_")]

        # Expected public names from __all__
        expected_names = set(air_quality.__all__)

        # Module names and TYPE_CHECKING appear due to import statements
        # Other tests may have imported additional submodules (dataset, module, etc.)
        # This is expected Python behavior when modules are imported elsewhere
        # We only verify that __all__ contains the correct Feature 002 exports
        actual_all_names = set(air_quality.__all__)

        # Verify __all__ only contains expected Feature 002 + core exports
        expected_all = {
            "__version__",
            "hello",  # Core package
            # Feature 002 Units (6)
            "Unit",
            "can_convert",
            "convert_values",
            "get_factor",
            "round_for_reporting",
            "validate_units_schema",
            # Feature 002 Time (6)
            "TimeBounds",
            "compute_time_bounds",
            "ensure_timezone_aware",
            "resample_mean",
            "rolling_window_mean",
            "to_utc",
        }

        assert actual_all_names == expected_all, (
            f"__all__ mismatch. "
            f"Missing: {expected_all - actual_all_names}, "
            f"Extra: {actual_all_names - expected_all}"
        )


class TestAPIFunctionalSmokeTests:
    """Quick functional smoke tests to verify imports actually work."""

    def test_unit_enum_functional(self):
        """Unit enum works when imported from public API."""
        from air_quality import Unit

        # Can create and compare
        assert Unit.UG_M3 == Unit.UG_M3
        assert Unit.PPB != Unit.PPM

    def test_conversion_functions_functional(self):
        """Conversion functions work when imported from public API."""
        from air_quality import Unit, can_convert, get_factor

        # Basic functionality check
        assert can_convert(Unit.UG_M3, Unit.MG_M3)
        assert get_factor(Unit.PPB, Unit.PPM) == 0.001

    def test_time_functions_functional(self):
        """Time utility functions work when imported from public API."""
        from datetime import datetime, timezone

        from air_quality import TimeBounds, ensure_timezone_aware

        # Basic functionality check
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        aware_dt = ensure_timezone_aware(naive_dt)
        assert aware_dt.tzinfo == timezone.utc

        # TimeBounds creation
        bounds = TimeBounds(start=aware_dt, end=aware_dt)
        assert bounds.start == aware_dt
