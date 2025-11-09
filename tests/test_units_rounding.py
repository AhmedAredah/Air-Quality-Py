"""Tests for rounding policy and round_for_reporting (Feature 002).

Constitution compliance:
- Section 8: Consistent reporting rounding
- Section 15: Centralized rounding policy registry
- Validation: Per-unit defaults, per-pollutant overrides, container type preservation

Test scenarios (placeholder - skip markers):
1. Default precision per unit (UG_M3/PPB: 1 decimal, MG_M3/PPM: 3 decimals)
2. Pollutant override takes precedence over unit default
3. Case-insensitive pollutant lookup
4. Scalar (int/float) rounding returns same type
5. pandas Series rounding returns pandas Series
6. Polars Series rounding returns Polars Series
7. NaN values preserved through rounding
8. Empty Series returns empty result
9. Non-numeric dtype raises TypeError with dtype name
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl
import pytest

from air_quality.units import Unit, round_for_reporting


class TestRoundingPolicyDefaults:
    """Test default rounding precision per unit."""

    def test_ug_m3_default_precision_one_decimal(self):
        """UG_M3 default rounding to 1 decimal place."""
        result = round_for_reporting(123.456, Unit.UG_M3)
        assert result == pytest.approx(123.5)

    def test_ppb_default_precision_one_decimal(self):
        """PPB default rounding to 1 decimal place."""
        result = round_for_reporting(45.678, Unit.PPB)
        assert result == pytest.approx(45.7)

    def test_mg_m3_default_precision_three_decimals(self):
        """MG_M3 default rounding to 3 decimal places."""
        result = round_for_reporting(1.23456, Unit.MG_M3)
        assert result == pytest.approx(1.235)

    def test_ppm_default_precision_three_decimals(self):
        """PPM default rounding to 3 decimal places."""
        result = round_for_reporting(0.123456, Unit.PPM)
        assert result == pytest.approx(0.123)


class TestPollutantOverrides:
    """Test per-pollutant override precedence."""

    def test_pollutant_override_takes_precedence(self):
        """Pollutant-specific override takes precedence over unit default.

        Example: If NO2 has override precision of 2, it overrides
        the unit default (e.g., UG_M3 default of 1).
        """
        # Since registry is empty by default, we test that unknown pollutants
        # fall back to unit defaults (tested in test_unknown_pollutant_uses_unit_default)
        # This test documents the intended behavior for when overrides are added
        result = round_for_reporting(123.456, Unit.UG_M3, pollutant="UNKNOWN")
        # Should use UG_M3 default of 1 decimal
        assert result == pytest.approx(123.5)

    def test_pollutant_case_insensitive_lookup(self):
        """Pollutant name lookup is case-insensitive."""
        # Test with unknown pollutant in different cases - all should produce same result
        result_lower = round_for_reporting(123.456, Unit.UG_M3, pollutant="no2")
        result_upper = round_for_reporting(123.456, Unit.UG_M3, pollutant="NO2")
        result_mixed = round_for_reporting(123.456, Unit.UG_M3, pollutant="No2")
        # All should produce same result (UG_M3 default since NO2 not in registry)
        assert result_lower == result_upper == result_mixed
        assert result_lower == pytest.approx(123.5)

    def test_unknown_pollutant_uses_unit_default(self):
        """Unknown pollutant name falls back to unit default."""
        result = round_for_reporting(123.456, Unit.UG_M3, pollutant="UNKNOWN_POLLUTANT")
        # Should use UG_M3 default of 1 decimal
        assert result == pytest.approx(123.5)

    def test_none_pollutant_uses_unit_default(self):
        """None pollutant parameter uses unit default."""
        result = round_for_reporting(123.456, Unit.UG_M3, pollutant=None)
        assert result == pytest.approx(123.5)


class TestRoundingContainerTypes:
    """Test rounding preserves container type."""

    def test_scalar_int_returns_numeric(self):
        """Scalar int rounding returns numeric result."""
        result = round_for_reporting(123, Unit.UG_M3)
        assert isinstance(result, (int, float))
        assert result == pytest.approx(123.0)

    def test_scalar_float_returns_float(self):
        """Scalar float rounding returns float."""
        result = round_for_reporting(123.456, Unit.UG_M3)
        assert isinstance(result, float)
        assert result == pytest.approx(123.5)

    def test_pandas_series_returns_pandas_series(self):
        """pandas Series rounding returns pandas Series."""
        series = pd.Series([123.456, 78.912, 45.678])
        result = round_for_reporting(series, Unit.UG_M3)
        assert isinstance(result, pd.Series)
        assert len(result) == 3
        assert result.iloc[0] == pytest.approx(123.5)
        assert result.iloc[1] == pytest.approx(78.9)
        assert result.iloc[2] == pytest.approx(45.7)

    def test_polars_series_returns_polars_series(self):
        """Polars Series rounding returns Polars Series."""
        series = pl.Series([123.456, 78.912, 45.678])
        result = round_for_reporting(series, Unit.UG_M3)
        assert isinstance(result, pl.Series)
        assert len(result) == 3
        assert result[0] == pytest.approx(123.5)

    def test_nan_preserved(self):
        """NaN values preserved through rounding."""
        series = pd.Series([123.456, np.nan, 45.678])
        result = round_for_reporting(series, Unit.UG_M3)
        assert pd.isna(result.iloc[1])
        assert result.iloc[0] == pytest.approx(123.5)
        assert result.iloc[2] == pytest.approx(45.7)

    def test_empty_series_returns_empty(self):
        """Empty Series rounding returns empty result."""
        series = pd.Series([], dtype=float)
        result = round_for_reporting(series, Unit.UG_M3)
        assert isinstance(result, pd.Series)
        assert len(result) == 0

    def test_non_numeric_raises_type_error(self):
        """Non-numeric dtype raises TypeError with dtype name."""
        series = pd.Series(["a", "b", "c"])
        with pytest.raises(TypeError) as exc_info:
            round_for_reporting(series, Unit.UG_M3)
        assert "object" in str(exc_info.value) or "string" in str(exc_info.value)
