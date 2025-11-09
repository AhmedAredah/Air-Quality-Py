# Feature 002 Requirements Checklist

Status: Draft

Legend: [ ] Pending  [x] Verified  [! ] Needs Clarification

Constitution Gate: No implementation may proceed until this checklist is fully satisfied for Sections 3, 7, 8, 9, 10, 11, and 15 of the Constitution.

## Functional Requirements (Units) — Sec 9, Sec 11, Sec 15

- [ ] FR-U01 Enum defined with all members
- [ ] FR-U02 Unit.parse raises UnitError on invalid
- [ ] FR-U03 can_convert handles identity & defined
- [ ] FR-U04 get_factor raises UnitError unsupported
- [ ] FR-U05 convert_values preserves container type
- [ ] FR-U06 round_for_reporting precision rules
- [ ] FR-U07 validate_units_schema normalizes / errors include column
- [ ] FR-U08 Type annotations complete (no Any)

## Functional Requirements (Time Utilities) — Sec 3, Sec 10, Sec 11

- [ ] FR-T01 TimeBounds dataclass UTC aware
- [ ] FR-T02 ensure_timezone_aware sets UTC if naive
- [ ] FR-T03 to_utc converts aware to UTC
- [ ] FR-T04 compute_time_bounds single collect
- [ ] FR-T05 resample_mean numeric columns only
- [ ] FR-T06 rolling_window_mean centered, min_periods=1
- [ ] FR-T07 No row-wise Python loops

## Functional Requirements (Dataset Integration) — Sec 3, Sec 15

- [ ] FR-D01 Metadata column_units accepted
- [ ] FR-D02 column_units property returns mapping
- [ ] FR-D03 Invalid unit metadata raises UnitError
- [ ] FR-D04 Canonical columns logic unchanged

## Functional Requirements (Errors & Validation) — Sec 9

- [ ] FR-E01 Reuse UnitError only
- [ ] FR-E02 Conversion failure message includes src & dst
- [ ] FR-E03 Non-numeric types raise TypeError with type name

## Functional Requirements (Reporting & Provenance) — Sec 8, Sec 15

- [ ] FR-R01 Pure conversion/rounding (no mutation)
- [ ] FR-R02 compute_time_bounds deterministic
- [ ] FR-R03 Docstrings reference constitution sections

## Non-Functional Requirements — Sec 11

- [ ] NFR-P01 1M length conversion < 50 ms (smoke)
- [ ] NFR-T01 No new deps added
- [ ] NFR-Q01 Mypy passes clean
- [ ] NFR-D01 Public API surface size constraint
- [ ] NFR-M01 Only one collect in compute_time_bounds

## Edge Cases

- [ ] EC1 Identity conversion returns same object/value
- [ ] EC2 Empty Series conversion returns empty
- [ ] EC3 NaN preserved in conversion & rounding
- [ ] EC4 Non-datetime column time_bounds surfaces underlying error
- [ ] EC5 window=1 rolling returns original numeric values
- [ ] EC6 Resample coerces non-datetime to UTC
- [ ] EC7 Invalid unit key metadata raises UnitError

## Acceptance Criteria

- [ ] AC1 All FR items satisfied
- [ ] AC2 All tests created & passing
- [ ] AC3 Mypy clean
- [ ] AC4 Existing tests still green
- [ ] AC5 README section updated
- [ ] AC6 Perf smoke documented

## Open Questions

- [! ] Q1 Kelvin/Celsius include now?
- [! ] Q2 Units in provenance automatically?
- [! ] Q3 Frequency inference for resampling?

## Sign-off

| Reviewer    | Date | Notes |
|-------------|------|-------|
| Stakeholder |      |       |
| Engineering |      |       |
| QA          |      |       |
