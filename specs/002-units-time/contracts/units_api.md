# Contracts — Units API (Feature 002)

Status: Phase 1 — Contracts
Date: 2025-11-08

These are API contracts only. No implementation code here.

## Contract style
- Inputs/outputs fully typed conceptually.
- Error modes listed and mapped to Constitution Sec 9.
- Pure functions; no mutation.

## Functions

### parse
- Signature: `Unit parse(value: str | Unit)`
- Behavior: Returns `Unit` if `value` is already a Unit; parses exact string tokens otherwise.
- Errors: `UnitError` on unknown token; message includes token.

### can_convert
- Signature: `bool can_convert(src: Unit, dst: Unit)`
- Behavior: True if identity or supported factor exists.
- Errors: None.

### get_factor
- Signature: `float get_factor(src: Unit, dst: Unit)`
- Behavior: Returns multiplicative factor such that `dst = src * factor`.
- Errors: `UnitError` if pair unsupported; message includes src/dst names.

### convert_values
- Signature: `Number|Series convert_values(values: Number|pd.Series|pl.Series, src: Unit, dst: Unit)`
- Behavior: Returns same container type; vectorized multiplication only; NaNs preserved.
- Errors: `UnitError` for unsupported pair; `TypeError` for non-numeric dtype.

### round_for_reporting
- Signature: `Number|Series round_for_reporting(values: Number|pd.Series|pl.Series, unit: Unit, pollutant: Optional[str] = None)`
- Behavior: Applies centralized rounding based on registry; pollutant override takes precedence.
- Errors: `TypeError` for non-numeric dtype.

### validate_units_schema
- Signature: `dict[str, Unit] validate_units_schema(mapping: dict[str, Unit | str])`
- Behavior: Normalizes str|Unit values to Unit; returns new dict.
- Errors: `UnitError` with offending column name in message for any invalid unit string.

## Non-Functional
- All functions are pure and type-annotated (no implicit Any).
- Performance: conversions are O(n) vectorized; no Python row loops (Sec 11).

---
End of units contracts