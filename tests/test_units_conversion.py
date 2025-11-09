"""Tests for unit conversion functions (Feature 002).

Constitution compliance:
- Section 10: Test coverage for conversion logic
- Section 11: Validate vectorized operations (no row loops)
- Validation: can_convert, get_factor, convert_values

Test scenarios (placeholder - skip markers):
1. Identity conversion (same src/dst) returns input unchanged
2. ug/m3 ↔ mg/m3 conversion uses correct factor (1000x)
3. ppm ↔ ppb conversion uses correct factor (1000x)
4. Unsupported conversion pairs raise UnitError with src/dst in message
5. NaN values preserved through conversion
6. Empty Series returns empty result
7. Scalar (int/float) conversion returns same type
8. pandas Series conversion returns pandas Series
9. Polars Series conversion returns Polars Series
10. Non-numeric dtype raises TypeError with dtype name
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl
import pytest

from air_quality.exceptions import UnitError
from air_quality.units import Unit, can_convert, convert_values, get_factor


class TestCanConvert:
    """Test can_convert function."""

    def test_identity_conversion_supported(self):
        """Identity conversion (same src and dst) always supported."""
        assert can_convert(Unit.UG_M3, Unit.UG_M3) is True
        assert can_convert(Unit.PPM, Unit.PPM) is True

    def test_defined_conversions_supported(self):
        """Defined conversion pairs are supported."""
        # Mass concentration conversions
        assert can_convert(Unit.UG_M3, Unit.MG_M3) is True
        assert can_convert(Unit.MG_M3, Unit.UG_M3) is True
        # Volume concentration conversions
        assert can_convert(Unit.PPM, Unit.PPB) is True
        assert can_convert(Unit.PPB, Unit.PPM) is True

    def test_unsupported_conversions_not_supported(self):
        """Cross-type conversions (mass ↔ volume) not supported."""
        assert can_convert(Unit.UG_M3, Unit.PPM) is False
        assert can_convert(Unit.PPM, Unit.MG_M3) is False


class TestGetFactor:
    """Test get_factor function."""

    def test_identity_factor_is_one(self):
        """Identity conversion has factor of 1.0."""
        assert get_factor(Unit.UG_M3, Unit.UG_M3) == 1.0
        assert get_factor(Unit.PPM, Unit.PPM) == 1.0

    def test_ug_to_mg_factor(self):
        """ug/m3 to mg/m3 factor is 0.001 (divide by 1000)."""
        assert get_factor(Unit.UG_M3, Unit.MG_M3) == 0.001

    def test_mg_to_ug_factor(self):
        """mg/m3 to ug/m3 factor is 1000."""
        assert get_factor(Unit.MG_M3, Unit.UG_M3) == 1000.0

    def test_ppm_to_ppb_factor(self):
        """ppm to ppb factor is 1000."""
        assert get_factor(Unit.PPM, Unit.PPB) == 1000.0

    def test_ppb_to_ppm_factor(self):
        """ppb to ppm factor is 0.001."""
        assert get_factor(Unit.PPB, Unit.PPM) == 0.001

    def test_unsupported_raises_unit_error(self):
        """Unsupported pair raises UnitError with src/dst in message."""
        with pytest.raises(UnitError) as exc_info:
            get_factor(Unit.UG_M3, Unit.PPM)
        error_msg = str(exc_info.value)
        assert "ug/m3" in error_msg or "UG_M3" in error_msg
        assert "ppm" in error_msg or "PPM" in error_msg


class TestConvertValues:
    """Test convert_values function."""

    def test_scalar_int_conversion(self):
        """Scalar int conversion returns numeric result."""
        result = convert_values(1000, Unit.UG_M3, Unit.MG_M3)
        assert isinstance(result, (int, float))
        assert result == pytest.approx(1.0)

    def test_scalar_float_conversion(self):
        """Scalar float conversion returns float."""
        result = convert_values(1500.5, Unit.UG_M3, Unit.MG_M3)
        assert isinstance(result, float)
        assert result == pytest.approx(1.5005)

    def test_pandas_series_conversion(self):
        """pandas Series conversion returns pandas Series."""
        series = pd.Series([100.0, 200.0, 300.0])
        result = convert_values(series, Unit.UG_M3, Unit.MG_M3)
        assert isinstance(result, pd.Series)
        assert len(result) == 3
        assert result.iloc[0] == pytest.approx(0.1)
        assert result.iloc[1] == pytest.approx(0.2)
        assert result.iloc[2] == pytest.approx(0.3)

    def test_polars_series_conversion(self):
        """Polars Series conversion returns Polars Series."""
        series = pl.Series([100.0, 200.0, 300.0])
        result = convert_values(series, Unit.UG_M3, Unit.MG_M3)
        assert isinstance(result, pl.Series)
        assert len(result) == 3
        assert result[0] == pytest.approx(0.1)

    def test_nan_preserved(self):
        """NaN values are preserved through conversion."""
        series = pd.Series([100.0, np.nan, 300.0])
        result = convert_values(series, Unit.UG_M3, Unit.MG_M3)
        assert pd.isna(result.iloc[1])
        assert result.iloc[0] == pytest.approx(0.1)
        assert result.iloc[2] == pytest.approx(0.3)

    def test_empty_series_returns_empty(self):
        """Empty Series conversion returns empty result."""
        series = pd.Series([], dtype=float)
        result = convert_values(series, Unit.UG_M3, Unit.MG_M3)
        assert isinstance(result, pd.Series)
        assert len(result) == 0

    def test_identity_conversion_returns_same_object(self):
        """Identity conversion returns input unchanged (optimization)."""
        series = pd.Series([100.0, 200.0])
        result = convert_values(series, Unit.UG_M3, Unit.UG_M3)
        # Should return same values
        pd.testing.assert_series_equal(result, series)

    def test_unsupported_conversion_raises_unit_error(self):
        """Unsupported conversion raises UnitError."""
        with pytest.raises(UnitError):
            convert_values(100.0, Unit.UG_M3, Unit.PPM)

    def test_non_numeric_raises_type_error(self):
        """Non-numeric dtype raises TypeError with dtype name."""
        series = pd.Series(["a", "b", "c"])
        with pytest.raises(TypeError) as exc_info:
            convert_values(series, Unit.UG_M3, Unit.MG_M3)
        assert "object" in str(exc_info.value) or "string" in str(exc_info.value)
