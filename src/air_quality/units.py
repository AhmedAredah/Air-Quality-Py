"""air_quality.units

Central units registry and conversion utilities for concentration measurements.

Constitution compliance:
- Section 9: UnitError for parsing/conversion failures; typed API (no Any)
- Section 11: Vectorized operations only; no row-wise Python loops
- Section 15: Central units registry with rounding policy

This module provides:
- Unit Enum: controlled vocabulary for supported concentration units
- Conversion utilities: deterministic, vectorized conversions
- Rounding policy: centralized per-unit defaults with optional per-pollutant overrides
- Schema validation: normalize dataset unit metadata with fail-fast error handling
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional, Union

import pandas as pd
import polars as pl

from .exceptions import UnitError


class TimeUnit(str, Enum):
    """Time units for trend analysis with calendar-aware semantics.

    Constitution References
    -----------------------
    - Section 3: Time unit standards for temporal analysis
    - Section 15: Centralized time unit definitions

    Time Unit Semantics
    -------------------
    These units follow calendar-aware semantics for trend analysis:

    HOUR : str
        1 hour elapsed time (3600 seconds).
        Use for high-frequency data (hourly observations).

    DAY : str
        1 calendar day (24 hours).
        Use for daily aggregations and short-term trends.

    CALENDAR_MONTH : str
        1 calendar month (variable days: 28-31).
        Accounts for month-length variation.
        Use for monthly trends and seasonal analysis.

    CALENDAR_YEAR : str
        1 calendar year (365 or 366 days).
        Accounts for leap years.
        Use for annual trends and long-term analysis.

    Examples
    --------
    >>> TimeUnit.DAY.value
    'day'
    >>> TimeUnit.CALENDAR_YEAR.value
    'calendar_year'
    """

    HOUR = "hour"
    DAY = "day"
    CALENDAR_MONTH = "calendar_month"
    CALENDAR_YEAR = "calendar_year"


class UnitFamily(Enum):
    """Unit family classification for preventing invalid conversions.

    Units can only be converted within the same family.
    Constitution Section 15: Type-safe unit system.
    """

    MASS_CONCENTRATION = "mass_concentration"
    VOLUME_CONCENTRATION = "volume_concentration"


class Unit(Enum):
    """Supported concentration units for air quality measurements.

    Each unit is defined as a tuple: (symbol, family, to_base_factor, reporting_precision)
    - symbol: Human-readable unit string
    - family: UnitFamily enum member
    - to_base_factor: Conversion factor to the base unit of the family
    - reporting_precision: Default decimal places for reporting/rounding

    Base units:
    - MASS_CONCENTRATION: ug/m3 (factor = 1.0, precision = 1)
    - VOLUME_CONCENTRATION: ppb (factor = 1.0, precision = 1)

    Constitution Section 15: Central units registry; free-form units prohibited.
    Constitution Section 8: Consistent reporting rounding.

    Members
    -------
    UG_M3 : tuple
        Micrograms per cubic meter - base unit for mass concentration
    MG_M3 : tuple
        Milligrams per cubic meter - 1000x ug/m3
    PPM : tuple
        Parts per million - 1000x ppb
    PPB : tuple
        Parts per billion - base unit for volume concentration
    """

    # (symbol, family, to_base_factor, reporting_precision)
    # MASS_CONCENTRATION family: base unit is ug/m3
    UG_M3 = ("ug/m3", UnitFamily.MASS_CONCENTRATION, 1.0, 1)
    MG_M3 = ("mg/m3", UnitFamily.MASS_CONCENTRATION, 1000.0, 3)  # 1 mg/m3 = 1000 ug/m3

    # VOLUME_CONCENTRATION family: base unit is ppb
    PPB = ("ppb", UnitFamily.VOLUME_CONCENTRATION, 1.0, 1)
    PPM = ("ppm", UnitFamily.VOLUME_CONCENTRATION, 1000.0, 3)  # 1 ppm = 1000 ppb

    @property
    def symbol(self) -> str:
        """Get the unit symbol string."""
        return self.value[0]

    @property
    def family(self) -> UnitFamily:
        """Get the unit family."""
        return self.value[1]

    @property
    def to_base_factor(self) -> float:
        """Get conversion factor to base unit of this family."""
        return self.value[2]

    @property
    def reporting_precision(self) -> int:
        """Get default decimal places for reporting."""
        return self.value[3]

    @classmethod
    def parse(cls, value: Union[str, Unit]) -> Unit:
        """Parse a string or Unit into a Unit enum member.

        Parameters
        ----------
        value : str | Unit
            String token (exact match required) or existing Unit instance.

        Returns
        -------
        Unit
            Normalized Unit enum member.

        Raises
        ------
        UnitError
            If value is an unknown string token.

        Examples
        --------
        >>> Unit.parse("ug/m3")
        <Unit.UG_M3: 'ug/m3'>
        >>> Unit.parse(Unit.PPM)
        <Unit.PPM: 'ppm'>
        """
        # If already a Unit instance, return as-is
        if isinstance(value, Unit):
            return value

        # Match string value to unit symbol
        for member in cls:
            if member.symbol == value:
                return member

        # No match found - raise UnitError with helpful message
        valid_units = ", ".join(f"'{m.symbol}'" for m in cls)
        raise UnitError(f"Invalid unit '{value}'. Valid units are: {valid_units}")


# Rounding policy per-pollutant overrides (read-only at runtime)
# Constitution Section 15: centralized rounding policy
# Unit-level defaults are embedded in Unit enum (reporting_precision property)
_ROUNDING_POLICY_PER_POLLUTANT: Dict[str, int] = {
    # Optional per-pollutant overrides (case-insensitive keys by convention)
    # Keys should be uppercase for consistent case-insensitive lookup
    # Example: "NO2": 2 would override unit default for NO2 to 2 decimal places
    # "NO2": 2,  # Override example: NO2 reported with 2 decimals regardless of unit
}


def can_convert(src: Unit, dst: Unit) -> bool:
    """Check if conversion between two units is supported.

    Units must be in the same family (e.g., both mass or both volume concentration).
    Constitution Section 11: Pure function; no side effects.
    Constitution Section 15: Type-safe unit system prevents cross-family conversions.

    Parameters
    ----------
    src : Unit
        Source unit.
    dst : Unit
        Destination unit.

    Returns
    -------
    bool
        True if identity or defined conversion factor exists; False otherwise.

    Examples
    --------
    >>> can_convert(Unit.UG_M3, Unit.MG_M3)
    True
    >>> can_convert(Unit.UG_M3, Unit.PPM)  # Different families
    False
    """
    # Identity conversion always supported
    if src == dst:
        return True

    # Check if units are in the same family
    return src.family == dst.family


def get_factor(src: Unit, dst: Unit) -> float:
    """Get multiplicative conversion factor from src to dst.

    Factor such that: dst_value = src_value * factor
    Units must be in the same family (prevents mass ↔ volume conversions).

    Constitution Section 9: UnitError includes src/dst in message.
    Constitution Section 15: Type-safe unit system prevents cross-family conversions.

    Parameters
    ----------
    src : Unit
        Source unit.
    dst : Unit
        Destination unit.

    Returns
    -------
    float
        Conversion factor.

    Raises
    ------
    UnitError
        If conversion pair is unsupported or units are from different families.

    Examples
    --------
    >>> get_factor(Unit.UG_M3, Unit.MG_M3)
    0.001
    >>> get_factor(Unit.UG_M3, Unit.PPM)  # Raises UnitError
    """
    # Identity conversion
    if src == dst:
        return 1.0

    # Check if units are in the same family
    if src.family != dst.family:
        raise UnitError(
            f"Cannot convert between different unit families: "
            f"{src.symbol} ({src.family.value}) and {dst.symbol} ({dst.family.value}). "
            f"Mass concentration units (ug/m3, mg/m3) cannot be converted to "
            f"volume concentration units (ppm, ppb) without additional parameters."
        )

    # Convert via base unit: src → base → dst
    # factor = (src_to_base) / (dst_to_base)
    # Example: mg/m3 → ug/m3 = 1000.0 / 1.0 = 1000.0
    return src.to_base_factor / dst.to_base_factor


def convert_values(
    values: Union[int, float, pd.Series, pl.Series],
    src: Unit,
    dst: Unit,
) -> Union[int, float, pd.Series, pl.Series]:
    """Convert values from src unit to dst unit (vectorized).

    Returns same container type as input. NaNs are preserved.
    Constitution Section 11: Vectorized multiplication only; no row loops.

    Parameters
    ----------
    values : int | float | pd.Series | pl.Series
        Scalar or Series of concentration values.
    src : Unit
        Source unit of input values.
    dst : Unit
        Destination unit for output.

    Returns
    -------
    int | float | pd.Series | pl.Series
        Converted values in same container type as input.

    Raises
    ------
    UnitError
        If conversion is unsupported.
    TypeError
        If values dtype is non-numeric; message includes dtype name.

    Examples
    --------
    >>> convert_values(1000.0, Unit.UG_M3, Unit.MG_M3)
    1.0
    >>> series = pd.Series([100, 200, float('nan')])
    >>> convert_values(series, Unit.UG_M3, Unit.MG_M3)
    0    0.1
    1    0.2
    2    NaN
    dtype: float64
    """
    # Get conversion factor (may raise UnitError)
    factor = get_factor(src, dst)

    # Identity conversion optimization - return unchanged
    if factor == 1.0:
        return values

    # Type validation and vectorized conversion
    if isinstance(values, (int, float)):
        # Scalar conversion
        return values * factor

    elif isinstance(values, pd.Series):
        # pandas Series - vectorized multiplication (preserves NaN)
        if not pd.api.types.is_numeric_dtype(values.dtype):
            raise TypeError(
                f"Cannot convert non-numeric dtype {values.dtype}. "
                f"Expected numeric dtype for unit conversion."
            )
        return values * factor

    elif isinstance(values, pl.Series):
        # Polars Series - vectorized multiplication
        if not values.dtype.is_numeric():
            raise TypeError(
                f"Cannot convert non-numeric dtype {values.dtype}. "
                f"Expected numeric dtype for unit conversion."
            )
        return values * factor

    else:
        raise TypeError(
            f"Unsupported type {type(values).__name__}. "
            f"Expected int, float, pd.Series, or pl.Series."
        )


def round_for_reporting(
    values: Union[int, float, pd.Series, pl.Series],
    unit: Unit,
    pollutant: Optional[str] = None,
) -> Union[int, float, pd.Series, pl.Series]:
    """Apply centralized rounding policy for reporting.

    Pollutant override takes precedence over per-unit default.
    Constitution Section 8: Consistent reporting rounding.
    Constitution Section 15: Centralized rounding policy.

    Parameters
    ----------
    values : int | float | pd.Series | pl.Series
        Values to round.
    unit : Unit
        Unit of values (determines default precision).
    pollutant : str, optional
        Pollutant name for optional override lookup (case-insensitive).

    Returns
    -------
    int | float | pd.Series | pl.Series
        Rounded values in same container type.

    Raises
    ------
    TypeError
        If values dtype is non-numeric.

    Examples
    --------
    >>> round_for_reporting(1.2345, Unit.UG_M3)
    1.2
    >>> round_for_reporting(0.123456, Unit.MG_M3)
    0.123
    """
    # Determine precision: pollutant override > unit default
    precision = unit.reporting_precision

    if pollutant is not None:
        # Case-insensitive lookup for pollutant override
        pollutant_upper = pollutant.upper()
        if pollutant_upper in _ROUNDING_POLICY_PER_POLLUTANT:
            precision = _ROUNDING_POLICY_PER_POLLUTANT[pollutant_upper]

    # Round based on container type
    if isinstance(values, (int, float)):
        # Scalar rounding
        return round(values, precision)

    elif isinstance(values, pd.Series):
        # pandas Series rounding
        # Check if dtype is numeric
        if not pd.api.types.is_numeric_dtype(values.dtype):
            raise TypeError(
                f"Non-numeric dtype not supported for rounding. "
                f"Expected numeric dtype, got {values.dtype}"
            )
        # Round preserving NaNs
        return values.round(precision)

    elif isinstance(values, pl.Series):
        # Polars Series rounding
        # Check if dtype is numeric
        if not values.dtype.is_numeric():
            raise TypeError(
                f"Non-numeric dtype not supported for rounding. "
                f"Expected numeric dtype, got {values.dtype}"
            )
        # Round using Polars expression
        return values.round(precision)

    else:
        raise TypeError(
            f"Unsupported type {type(values).__name__}. "
            f"Expected int, float, pd.Series, or pl.Series."
        )


def validate_units_schema(mapping: Dict[str, Union[Unit, str]]) -> Dict[str, Unit]:
    """Normalize and validate dataset unit metadata.

    Converts str|Unit values to Unit enum members. Fail-fast on invalid.
    Constitution Section 3: Metadata normalization at dataset construction.
    Constitution Section 9: UnitError includes offending column name.

    Parameters
    ----------
    mapping : dict[str, Unit | str]
        Column name -> unit mapping (str values will be parsed).

    Returns
    -------
    dict[str, Unit]
        Normalized mapping with all values as Unit enum members.

    Raises
    ------
    UnitError
        If any unit string is invalid; error message includes column name.

    Examples
    --------
    >>> validate_units_schema({"conc": "ug/m3", "unc": Unit.UG_M3})
    {"conc": <Unit.UG_M3: 'ug/m3'>, "unc": <Unit.UG_M3: 'ug/m3'>}
    >>> validate_units_schema({"bad": "invalid_unit"})
    UnitError: Invalid unit 'invalid_unit' for column 'bad'
    """
    # Constitution Section 10: Immutability - return new dict
    normalized: Dict[str, Unit] = {}

    # Process each column's unit metadata
    # Constitution Section 3: Fail-fast validation (raise on first error)
    for column_name, unit_value in mapping.items():
        try:
            # Parse to Unit enum (handles both Unit and str inputs)
            normalized[column_name] = Unit.parse(unit_value)
        except UnitError as e:
            # Constitution Section 9: Include column context in error
            raise UnitError(f"Invalid unit for column '{column_name}': {str(e)}") from e

    return normalized


__all__ = [
    "TimeUnit",
    "Unit",
    "UnitFamily",
    "can_convert",
    "get_factor",
    "convert_values",
    "round_for_reporting",
    "validate_units_schema",
]
