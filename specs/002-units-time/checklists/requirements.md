# Feature 002 Requirements Checklist

Status: Draft

Legend: [ ] Pending  [x] Verified  [! ] Needs Clarification

Constitution Gate: No implementation may proceed until this checklist is fully satisfied for Sections 3, 7, 8, 9, 10, 11, and 15 of the Constitution.

## Functional Requirements (Units) — Sec 9, Sec 11, Sec 15

- [x] FR-U01 Enum defined with all members (data-model.md E1: UG_M3, MG_M3, PPM, PPB)
- [x] FR-U02 Unit.parse raises UnitError on invalid (contracts/units_api.md: parse function)
- [x] FR-U03 can_convert handles identity & defined (contracts/units_api.md: can_convert function)
- [x] FR-U04 get_factor raises UnitError unsupported (contracts/units_api.md: get_factor function)
- [x] FR-U05 convert_values preserves container type (contracts/units_api.md: convert_values returns same container)
- [x] FR-U06 round_for_reporting precision rules (data-model.md E2: RoundingPolicyRegistry with per_unit defaults + overrides)
- [x] FR-U07 validate_units_schema normalizes / errors include column (contracts/units_api.md: UnitError with column name)
- [x] FR-U08 Type annotations complete (no Any) (contracts/units_api.md: fully typed, no implicit Any)

## Functional Requirements (Time Utilities) — Sec 3, Sec 10, Sec 11

- [x] FR-T01 TimeBounds dataclass UTC aware (data-model.md E3: start/end tz-aware UTC, preserve precision)
- [x] FR-T02 ensure_timezone_aware sets UTC if naive (contracts/time_utils_api.md: ensure_timezone_aware)
- [x] FR-T03 to_utc converts aware to UTC (contracts/time_utils_api.md: to_utc function)
- [x] FR-T04 compute_time_bounds single collect (contracts/time_utils_api.md: Polars min/max, single collect)
- [x] FR-T05 resample_mean numeric columns only (contracts/time_utils_api.md: mean of numeric columns)
- [x] FR-T06 rolling_window_mean centered, min_periods=1 (contracts/time_utils_api.md: centered rolling, min_periods=1)
- [x] FR-T07 No row-wise Python loops (contracts specify vectorized ops only, Sec 11 compliance)

## Functional Requirements (Dataset Integration) — Sec 3, Sec 15

- [x] FR-D01 Metadata column_units accepted (data-model.md E4: column_units dict in metadata)
- [x] FR-D02 column_units property returns mapping (data-model.md E4: dict[str, Unit] exposed)
- [x] FR-D03 Invalid unit metadata raises UnitError (data-model.md E4: validate_units_schema raises with column name)
- [x] FR-D04 Canonical columns logic unchanged (spec.md FR-D04: no changes to existing schema logic)

## Functional Requirements (Errors & Validation) — Sec 9

- [x] FR-E01 Reuse UnitError only (spec.md FR-E01: UnitError from exceptions module, no new types)
- [x] FR-E02 Conversion failure message includes src & dst (contracts/units_api.md: get_factor/convert_values errors include units)
- [x] FR-E03 Non-numeric types raise TypeError with type name (contracts specify TypeError for non-numeric)

## Functional Requirements (Reporting & Provenance) — Sec 8, Sec 15

- [x] FR-R01 Pure conversion/rounding (no mutation) (contracts specify pure functions, immutability; spec.md FR-R01)
- [x] FR-R02 compute_time_bounds deterministic (spec.md FR-R02: deterministic given dataset content)
- [x] FR-R03 Docstrings reference constitution sections (spec.md FR-R03: brief docstrings with references)

## Non-Functional Requirements — Sec 11

- [x] NFR-P01 1M length conversion < 50 ms (smoke) ✅ **VERIFIED Phase 10**: 1M rows convert in ~2ms (25x better than 50ms target)
- [x] NFR-T01 No new deps added (spec.md NFR-T01: no additional dependencies)
- [x] NFR-Q01 Mypy passes clean (verified: units.py and time_utils.py pass mypy with no issues)
- [x] NFR-D01 Public API surface size constraint (spec.md NFR-D01: ≤7 functions + 1 Enum + 1 dataclass + 1 property)
- [x] NFR-M01 Only one collect in compute_time_bounds ✅ **VERIFIED Phase 10**: Single aggregation confirmed via performance tests

## Edge Cases

- [x] EC1 Identity conversion returns same object/value (contracts/units_api.md: can_convert supports identity)
- [x] EC2 Empty Series conversion returns empty (contracts: returns same container type)
- [x] EC3 NaN preserved in conversion & rounding (contracts/units_api.md: convert_values preserves NaNs)
- [x] EC4 Non-datetime column time_bounds surfaces underlying error (contracts/time_utils_api.md: errors not masked)
- [x] EC5 window=1 rolling returns original numeric values (contracts: min_periods=1 behavior)
- [x] EC6 Resample coerces non-datetime to UTC (contracts/time_utils_api.md: datetime handling)
- [x] EC7 Invalid unit key metadata raises UnitError (data-model.md E4: validate_units_schema raises)

## Acceptance Criteria

- [x] AC1 All FR items satisfied (all FR specs verified in design docs)
- [x] AC2 All tests created & passing ✅ **COMPLETE Phase 9**: 203/203 tests passing (100%)
- [x] AC3 Mypy clean ✅ **COMPLETE Phase 9**: All modules pass mypy --strict
- [x] AC4 Existing tests still green ✅ **COMPLETE Phase 8**: 18/18 dataset tests passing (no regressions)
- [x] AC5 README section updated ✅ **COMPLETE Phase 11**: Working examples with pandas/polars, performance metrics added
- [x] AC6 Perf smoke documented ✅ **COMPLETE Phase 10**: Performance results in HANDOFF.md

## Open Questions

- [x] Q1 Kelvin/Celsius include now? → **Resolved**: Out of scope for 002 per research.md D5; future feature with dimensional analysis
- [x] Q2 Units in provenance automatically? → **Resolved**: Deferred; attachment occurs in module run() paths per research.md
- [x] Q3 Frequency inference for resampling? → **Resolved**: Not included; explicit rule parameter required per research.md

## Sign-off

| Reviewer    | Date | Notes |
|-------------|------|-------|
| Stakeholder |      |       |
| Engineering |      |       |
| QA          |      |       |
