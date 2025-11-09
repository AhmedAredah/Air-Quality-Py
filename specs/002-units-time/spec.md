# Feature 002: Units & Time Primitives (Enum-Based)

Status: Draft
Last Updated: 2025-11-08
Owner: TBD

## Constitution Compliance Summary

This feature is designed under the air_quality Constitution v1.0.0. Key enforced sections:

- Section 3 (Data & Metadata Standards):
  - Columnar-first; time bounds computed with Polars and single collect.
  - Canonicalization and mapping metadata remain unchanged; unit metadata stored/validated explicitly.
- Section 7 (Core Architecture & AirQualityModule Interface):
  - Shared utilities (units/time) are centralized; no module-specific duplicates.
- Section 8 (Reporting & Visualization):
  - Rounding rules intended for consistent reporting; dashboard/CLI will consume standardized units/precision.
- Section 9 (API, Error Taxonomy & Docs):
  - Use existing `UnitError`; public APIs documented with types and exceptions.
- Section 10 (Testing, Reproducibility):
  - Tests planned for unit/rounding/time utilities; deterministic behavior.
- Section 11 (Performance & Scalability):
  - Vectorized conversions; avoid row-wise loops; single `.collect()` in bounds.
- Section 15 (Provenance, Units & Reproducibility):
  - Central units registry; clear rounding policy; ready for provenance attachment by modules.

## 1. Overview

Provide a minimal, deterministic, Enum-based foundation for handling measurement units (concentration) and core time operations (bounds, resampling, rolling statistics) across air quality datasets. Must reinforce constitution principles: columnar-first, DRY, provenance-friendly, no free-form strings for controlled vocabularies.

## Clarifications

### Session 2025-11-08

- Q: What rounding policy granularity should we adopt? → A: Per-unit defaults with optional per-pollutant overrides (centralized registry).
- Q: How should invalid dataset-level unit metadata be handled? → A: Fail fast at construction with UnitError including offending column name.
- Q: Which backend should power resampling utilities? → A: Use pandas at boundary functions (pandas resample) while keeping Polars as internal columnar core.

## 2. Goals

- G1: Enforce controlled vocabulary for supported units using an Enum (no raw strings in public APIs).
- G2: Enable safe, deterministic conversions among a minimal set of concentration units (ug/m3, mg/m3, ppm, ppb) with clear extensibility.
- G3: Provide reporting-friendly rounding conventions per unit type.
- G4: Offer reusable time utility functions for computing dataset time bounds and performing resampling / rolling means while respecting UTC canonical storage.
- G5: Integrate unit metadata at the dataset-level (e.g., `TimeSeriesDataset.column_units`) without breaking existing tests and architecture.
- G6: Maintain mypy/type-check cleanliness (no Any proliferation) and avoid performance regressions (O(n) vectorized operations only; never row loops).

## 3. Non-Goals

- NG1: Full scientific unit system (no handling of temperature, pressure, flow).
- NG2: Automatic detection of units from column names or values.
- NG3: Persisting units in provenance (may be added later in Feature 003+).
- NG4: Complex timezone handling beyond UTC standardization and naive -> aware conversion.

## 4. User Scenarios

### US1: Basic Unit Conversion

A QC analyst loads a dataset with concentration in micrograms per cubic meter and needs mg/m3 for a downstream health risk module.

### US2: Dashboard Reporting Rounding

An operations engineer produces a dashboard; wants consistent rounding across pollutants (ug/m3 to 0.1 precision, mg/m3 to 0.001, ppm to 0.001, ppb to 0.1).

### US3: Time Bounds for Metadata

An ingestion module attaches start/end timestamps to metadata for provenance and reporting.

### US4: Hourly Resampling

A user has irregular minute-level data and wants hourly mean concentrations with minimal code.

### US5: Rolling Mean QC Flagging

A QC module computes a centered rolling mean to detect sudden spikes compared to local baseline.

### US6: Multi-Column Unit Metadata

A dataset contains multiple concentration columns (conc, conc_unc); user supplies units metadata; later modules retrieve standardized Unit enums.

## 5. Functional Requirements

Each requirement gets an ID for checklist mapping.

### Units

Constitution references: Sections 9 (API & errors), 11 (performance), 15 (units registry).

- FR-U01: Provide `Unit` Enum with members: UG_M3("ug/m3"), MG_M3("mg/m3"), PPM("ppm"), PPB("ppb").
- FR-U02: Implement `Unit.parse(value: str | Unit) -> Unit` raising `UnitError` on invalid input.
- FR-U03: Implement `can_convert(src: Unit, dst: Unit) -> bool` supporting identity and defined factors.
- FR-U04: Implement `get_factor(src: Unit, dst: Unit) -> float` raising `UnitError` if unsupported.
- FR-U05: Implement `convert_values(values, src, dst)` accepting scalar (int|float) or vector (pandas Series, Polars Series) and returning same container type, using vectorized multiplication only.
- FR-U06: Implement `round_for_reporting(values, unit, pollutant: Optional[str] = None)` applying a centralized rounding policy: per-unit defaults with optional per-pollutant overrides. Defaults: UG_M3/PPB → 1 decimal; MG_M3/PPM → 3 decimals. When an override exists for `pollutant`, it takes precedence over unit default.
- FR-U07: Implement `validate_units_schema(mapping: dict[str, Unit | str]) -> dict[str, Unit]` returning normalized mapping or raising `UnitError` with column name context.
- FR-U08: All public unit API functions must be type annotated with no implicit Any.
- FR-U09: Provide a centralized rounding policy registry (read-only at runtime) that defines per-unit defaults and optional per-pollutant overrides; documented and testable.

### Time Utilities

Constitution references: Sections 3 (time/UTC), 11 (columnar/vectorized), 10 (testing & reproducibility).

- FR-T01: Implement `TimeBounds` dataclass with `start` and `end` (timezone-aware UTC datetimes).
- FR-T02: Implement `ensure_timezone_aware(dt)` adding UTC tzinfo if naive.
- FR-T03: Implement `to_utc(dt)` converting any aware datetime to UTC.
- FR-T04: Implement `compute_time_bounds(lazyframe, time_col="datetime") -> TimeBounds` using Polars min/max aggregation (single collect) and ensuring UTC.
- FR-T05: Implement `resample_mean(df, rule="1H", time_col="datetime")` using pandas resample, returning new DataFrame with mean of numeric columns only.
- FR-T06: Implement `rolling_window_mean(df, window=3, time_col="datetime")` producing centered rolling mean for numeric columns (min_periods=1) sorted by time.
- FR-T07: All time utilities must avoid row-wise Python loops over data rows (vectorized Pandas/Polars only).
- FR-T08: Resampling utilities MUST treat input DataFrame as immutable (no in-place mutation) and clearly document pandas boundary dependency.

### Dataset Integration

Constitution references: Sections 3 (canonical schema/metadata), 15 (units registry normalization).

- FR-D01: `TimeSeriesDataset` accepts optional metadata key `column_units` at construction; if present and dict, normalize via `validate_units_schema`.
- FR-D02: Provide `TimeSeriesDataset.column_units` property returning normalized mapping or None.
- FR-D03: Failed unit normalization during dataset init MUST raise `UnitError` (explicit, not silent) to prevent hidden metadata inconsistencies.
- FR-D04: No changes to existing dataset required canonical columns logic.
- FR-D05: UnitError raised for invalid column unit MUST include the column name in the error message for traceability.

### Error Handling & Validation

Constitution references: Section 9 (error taxonomy, docs).

- FR-E01: Reuse existing `UnitError` from exceptions module; never introduce new exception types for this feature.
- FR-E02: Error messages must include both source and destination units for conversion failures.
- FR-E03: Rounding and conversion must reject non-numeric dtypes with a TypeError mentioning unsupported type name.

### Reporting & Provenance Readiness

Constitution references: Sections 8 (reporting), 15 (provenance/units).

- FR-R01: All unit conversion and rounding functions are pure (no mutation of input objects).
- FR-R02: Time bounds function is deterministic given dataset content.
- FR-R03: Provide brief docstrings referencing constitution sections where applicable.

## 6. Non-Functional Requirements

- NFR-P01: Unit conversion of a 1M-length Series must complete in under 50 ms on baseline dev hardware (<1e6 simple multiplications) – smoke test only.
- NFR-T01: No additional dependencies beyond existing stack.
- NFR-Q01: 100% mypy pass (no new warnings or errors) after implementation.
- NFR-D01: Public API surface stays minimal (≤ 7 new functions + 1 Enum + 1 dataclass + 1 property).
- NFR-M01: Maintain columnar-first principle (only one `.collect()` in `compute_time_bounds`).

## 7. Data Shapes

- Scalars: float | int
- Vector: pandas.Series or polars.Series of numeric dtype
- Unit Mapping: dict[str, Unit]
- TimeBounds: { start: datetime (UTC), end: datetime (UTC) }

## 8. Edge Cases

- EC1: Conversion identity (src == dst) returns original values untouched.
- EC2: Empty Series input returns empty Series of same type.
- EC3: NaN values preserved during conversion/rounding.
- EC4: Non-datetime column passed to `compute_time_bounds` raises KeyError or Polars schema error (surface underlying error; do not mask).
- EC5: Rolling window with window=1 returns original numeric values.
- EC6: Resample on DataFrame lacking datetime dtype coerces to UTC via `pd.to_datetime`.
- EC7: Invalid unit key in `column_units` metadata raises `UnitError` with column name.
- EC8: If a pollutant-specific rounding override is defined, it supersedes the unit default.
- EC9: Resample functions do not alter original DataFrame (identity of non-time columns preserved; object equality by reference allowed to differ).

## 9. Acceptance Criteria

- AC1: All FR-Uxx, FR-Txx, FR-Dxx, FR-Exx satisfied and checked in requirements checklist.
- AC2: Added tests: `tests/test_units_enum.py`, `tests/test_units_conversion.py`, `tests/test_units_rounding.py`, `tests/test_time_bounds.py`, `tests/test_time_resample_roll.py` covering happy + edge cases.
- AC3: Mypy passes with zero errors for new code.
- AC4: Existing 73 tests remain green (no regressions).
- AC5: README gains short usage section (<= 20 lines) demonstrating unit conversion + time bounds.
- AC6: Performance smoke test (optional) demonstrates conversion speed target qualitatively.
- AC7: Rounding policy registry covered by tests showing per-unit default and pollutant override precedence.
- AC8: Dataset unit metadata validation tests assert UnitError message contains offending column name.
- AC9: Resample immutability test confirms original DataFrame unchanged and function returns a new object.

Constitution Check Gate: Implementation MAY NOT proceed until this spec passes a Constitution Check confirming adherence to Sections 3, 7, 8, 9, 10, 11, and 15.

## 10. Open Questions / Clarifications

1. Should we include Kelvin/Celsius conversions now? [NEEDS CLARIFICATION]
2. Should units be attached to provenance automatically? [NEEDS CLARIFICATION]
3. Is there a need for frequency inference (auto rule suggestion) in resampling? [NEEDS CLARIFICATION]

(Limit kept to three per instructions.)

## 11. Out of Scope (Future Work Candidates)

- Advanced time zone conversions (local site time <-> UTC).
- Full unit registry with dimensional analysis.
- Integration with pollutant/species Enum definitions (future Feature 003).
- Automatic QC flag generation that leverages rolling mean outputs.

## 12. Risk Analysis

- R1: Silent failure in unit normalization could propagate incorrect units -> Mitigation: FR-D03 mandates raising `UnitError`.
- R2: Performance overhead from repeated conversions -> Mitigation: pure multiplicative factors stored in dict, O(1) lookup.
- R3: Ambiguity expanding unit list later -> Mitigation: parse() uses exact value strings; extending requires explicit addition.

## 13. Test Plan Summary

- Enum parsing & invalid unit (FR-U02, FR-E02).
- Conversion ug/m3->mg/m3 round-trip identity (FR-U05, EC1).
- Conversion ppm<->ppb with factors + NaN preservation (FR-U05, EC3).
- Rounding precision distributions (FR-U06).
- Units schema validation with mixed str/Enum input (FR-U07, EC7).
- Time bounds on sample LazyFrame (FR-T04, EC4).
- Resample hourly means vs manual aggregation (FR-T05, EC6).
- Rolling mean center alignment & window=1 edge (FR-T06, EC5).
- Dataset integration raising on bad unit metadata (FR-D03).

## 14. Implementation Notes (Informational, not executed now)

- Place `units.py` and `time_utils.py` in `src/air_quality/`.
- Add imports in `__init__.py` optionally after approval.
- Ensure `TimeSeriesDataset` modification strictly additive (property + init path).

## 15. Approval Checklist Reference

See `checklists/requirements.md` for enumerated items mapped to FR/NFR IDs with space for verification signatures.

---
END OF SPEC
