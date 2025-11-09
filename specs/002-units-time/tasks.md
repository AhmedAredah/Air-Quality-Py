# Tasks — Feature 002: Units & Time Primitives (Enum-Based)

Status: Generated via speckit.tasks
Date: 2025-11-08

This tasks file is organized by phases and user stories. Each task follows the required checklist format.

## Phase 1 — Setup

- [ ] T001 Create feature docs directory structure at specs/002-units-time (already present; verify paths)
- [ ] T002 Add empty __init__.py guard files if needed in src/air_quality/ (confirm package integrity)

## Phase 2 — Foundational

- [ ] T003 Define placeholder exceptions import location in src/air_quality/exceptions.py (confirm UnitError exists)
- [ ] T004 Prepare stubs for units/time modules (no implementation): src/air_quality/units.py, src/air_quality/time_utils.py (docstrings + TODO only)
- [ ] T005 Ensure mypy configuration covers new files (pyproject.toml) and add type: py.typed marker already exists

## Phase 3 — User Stories (P1): US1 Basic Unit Conversion

Goal: Convert values between supported units deterministically using vectorized operations.
Independent test criteria: Identity conversion returns input; ug/m3↔mg/m3 and ppm↔ppb correct; NaNs preserved.

- [ ] T006 [US1] Add Unit Enum skeleton in src/air_quality/units.py (members only; no logic)
- [ ] T007 [US1] Add contracts docstrings for parse/can_convert/get_factor/convert_values in src/air_quality/units.py (raise NotImplementedError)
- [ ] T008 [US1] Wire public re-exports in src/air_quality/__init__.py for intended API names (commented or TODO only)
- [ ] T009 [US1] Create placeholder tests files in tests/test_units_enum.py and tests/test_units_conversion.py (skip markers; outline scenarios)

## Phase 4 — User Stories (P1): US2 Dashboard Reporting Rounding

Goal: Centralized rounding policy with per-unit defaults and optional per-pollutant overrides.
Independent test criteria: Overrides take precedence; default precisions applied correctly.

- [ ] T010 [US2] Add RoundingPolicyRegistry skeleton (dict constants) in src/air_quality/units.py (no functional code)
- [ ] T011 [US2] Add round_for_reporting signature and docstring in src/air_quality/units.py (raise NotImplementedError)
- [ ] T012 [US2] Add placeholder tests in tests/test_units_rounding.py (skip markers; outline overrides/defaults cases)

## Phase 5 — User Stories (P1): US3 Time Bounds for Metadata

Goal: Compute UTC-aware time bounds with preserved sub-second precision using Polars min/max with single collect.
Independent test criteria: tz-aware UTC outputs equal precise min/max in sample data.

- [ ] T013 [US3] Add TimeBounds dataclass skeleton in src/air_quality/time_utils.py (fields only)
- [ ] T014 [US3] Add compute_time_bounds signature and docstring in src/air_quality/time_utils.py (raise NotImplementedError)
- [ ] T015 [US3] Add placeholder tests in tests/test_time_bounds.py (skip markers; outline min/max UTC checks)

## Phase 6 — User Stories (P2): US4 Hourly Resampling

Goal: Boundary pandas resample mean; input immutability; numeric columns only.
Independent test criteria: Returns new DataFrame; respects rule parameter; datetime handling per contract.

- [ ] T016 [US4] Add resample_mean signature and docstring in src/air_quality/time_utils.py (raise NotImplementedError)
- [ ] T017 [US4] Add placeholder tests in tests/test_time_resample_roll.py (skip markers; outline resample checks)

## Phase 7 — User Stories (P2): US5 Rolling Mean QC Flagging

Goal: Centered rolling mean helper with min_periods=1 and pre-sort by time.
Independent test criteria: Window=1 equals original; centered alignment correct.

- [ ] T018 [US5] Add rolling_window_mean signature and docstring in src/air_quality/time_utils.py (raise NotImplementedError)
- [ ] T019 [US5] Extend tests in tests/test_time_resample_roll.py (skip markers; outline rolling cases)

## Phase 8 — User Stories (P2): US6 Multi-Column Unit Metadata

Goal: Normalize dataset unit metadata and expose property; fail fast on invalid units including offending column name.
Independent test criteria: UnitError raised with column context; None allowed when not provided.

- [ ] T020 [US6] Add validate_units_schema signature and docstring in src/air_quality/units.py (raise NotImplementedError)
- [ ] T021 [US6] Add integration touchpoint notes for TimeSeriesDataset in docs/specs (no code change now)
- [ ] T022 [US6] Add placeholder tests in tests/test_units_schema_validation.py (skip markers; outline invalid/valid cases)

## Final Phase — Polish & Cross-Cutting

- [ ] T023 Update README.md with brief usage note (<=20 lines) referencing quickstart.md paths
- [ ] T024 Ensure all new docs pass markdown lint (headings/lists) and run mypy dry-run (expect NotImplementedError in stubs)
- [ ] T025 Prepare tasks handoff summary and PR checklist (no remote push per user preference)

## Dependencies (story order)

- US1 → US2 → US6 (units first, then rounding, then dataset metadata)
- US3 → US4 → US5 (time bounds first, then resampling, then rolling)
- Units and Time tracks can proceed in parallel after foundational setup.

## Parallel execution examples

- [P] T006 [US1] Unit Enum skeleton in src/air_quality/units.py
- [P] T013 [US3] TimeBounds dataclass skeleton in src/air_quality/time_utils.py
- [P] T010 [US2] RoundingPolicyRegistry skeleton in src/air_quality/units.py

## Implementation strategy

- MVP scope: Complete US1 (enum + conversion contracts) and US3 (time bounds contracts) as first increment; keep functions unimplemented (raise NotImplementedError) per “specify-only” constraint until gated.
- Deliver incrementally per phase; convert placeholders to real tests/implementations only after constitution gate approval and explicit request to implement.
