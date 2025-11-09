# Data Model — Feature 002: Units & Time Primitives

Status: Phase 1 — Design
Date: 2025-11-08

This document extracts entities and validation rules from the spec for implementation planning. No code is implemented here.

## Entities

### E1. Unit (Enum)

- Members: UG_M3 ("ug/m3"), MG_M3 ("mg/m3"), PPM ("ppm"), PPB ("ppb").
- Parsing: `Unit.parse(value: str | Unit) -> Unit` (raises UnitError on unknown string).
- Conversion relations: identity + factors among supported pairs.
- Constraints: Free-form strings not accepted in public APIs; extensions are additive.

### E2. RoundingPolicyRegistry (read-only)

- Purpose: Central source of rounding precision for reporting.
- Fields:
  - per_unit: dict[Unit, int]  (e.g., {UG_M3:1, PPB:1, MG_M3:3, PPM:3})
  - per_pollutant_override: dict[str, int] (optional overrides, case-insensitive keys by convention)
- Behavior:
  - Lookup order: pollutant override (if provided and found) → per_unit default.
  - Exposed via pure functions; no mutation at runtime.

### E3. TimeBounds (dataclass)

- Fields: start: datetime (tz-aware UTC), end: datetime (tz-aware UTC)
- Invariant: Preserve full source precision; start <= end.

### E4. Dataset Integration (metadata)

- `column_units`: dict[str, Unit] attached to dataset metadata.
- Normalization: `validate_units_schema` converts str|Unit → Unit or raises UnitError listing offending column.

## API Surfaces

### Units API

- `can_convert(src: Unit, dst: Unit) -> bool`
- `get_factor(src: Unit, dst: Unit) -> float`  (UnitError if unsupported)
- `convert_values(values, src: Unit, dst: Unit)`  (scalar or Series; returns same container type; vectorized only)
- `round_for_reporting(values, unit: Unit, pollutant: Optional[str] = None)`  (applies registry)
- `validate_units_schema(mapping: dict[str, Unit | str]) -> dict[str, Unit]`

### Time API

- `ensure_timezone_aware(dt) -> datetime`
- `to_utc(dt) -> datetime`
- `compute_time_bounds(lazyframe, time_col: str = "datetime") -> TimeBounds` (Polars min/max, single collect)
- `resample_mean(df, rule: str = "1H", time_col: str = "datetime")`
- `rolling_window_mean(df, window: int = 3, time_col: str = "datetime")`

## Validation Rules

- Unit parsing rejects unknown strings (UnitError), test includes bad tokens.
- Conversion raises UnitError on unsupported pairs; error includes src/dst units.
- Numeric-only operations: non-numeric dtypes → TypeError mentioning dtype.
- Time bounds returns tz-aware UTC preserving sub-second precision.
- Resampling/rolling do not mutate input (new object returned).

## Relationships

- Dataset → column_units (0..1): optional; when present, must be normalized at construction.
- RoundingPolicyRegistry is global, read-only; used by `round_for_reporting` and dashboard/CLI presentational layers.

---
End of data-model design
