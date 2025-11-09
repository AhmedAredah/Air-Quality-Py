# Tasks — Feature 002: Units & Time Primitives (Implementation Phase)

Status: Implementation Phase - Generated from stub phase completion
Date: 2025-11-08

**Previous Phase**: Stub phase complete (T001-T025 all tasks ✅)  
**This Phase**: Implementation of all NotImplementedError stubs  
**Entry Criteria**: Constitution gate passed, 87 placeholder tests created, API contracts validated

This tasks file is organized by implementation phases. Each task converts stub functions to working implementations and enables the corresponding tests.

---

## Phase 1 — Pre-Implementation Validation

- [x] T100 Verify Constitution Check Gate passed for spec.md (Sections 3, 7, 8, 9, 10, 11, 15)
- [x] T101 Verify all 87 placeholder tests are properly skipped with reason markers
- [x] T102 Run mypy to confirm type signatures are complete before implementation
- [x] T103 Review constitution compliance checklist (42/48 verified items) and HANDOFF.md
- [x] T104 Verify checklists/requirements.md exists and maps all 48 FR/NFR items

## Phase 2 — Core Units Implementation (US1: Basic Unit Conversion)

Goal: Implement Unit.parse(), can_convert(), get_factor(), convert_values() to enable deterministic unit conversions.
Independent test criteria: Identity conversion works; ug/m3↔mg/m3 and ppm↔ppb conversions correct; NaNs preserved; type errors on non-numeric.

- [x] T201 [US1] Implement Unit.parse() classmethod in src/air_quality/units.py handling str/Unit input and raising UnitError on invalid
- [x] T202 [US1] Implement can_convert() function supporting identity and defined conversion pairs in src/air_quality/units.py
- [x] T203 [US1] Implement get_factor() function with conversion factor lookup dict in src/air_quality/units.py (raise UnitError if unsupported)
- [x] T204 [US1] Implement convert_values() function with scalar/Series type detection and vectorized multiplication in src/air_quality/units.py
- [x] T205 [US1] Remove skip markers from tests/test_units_enum.py (6 tests)
- [x] T206 [US1] Remove skip markers from tests/test_units_conversion.py (18 tests)
- [x] T207 [US1] Run pytest on test_units_enum.py and test_units_conversion.py to verify all 24 tests pass
- [x] T208 [US1] Run mypy to confirm no type regressions in units.py

## Phase 3 — Rounding Policy Implementation (US2: Dashboard Reporting Rounding)

Goal: Implement round_for_reporting() with centralized per-unit defaults and per-pollutant overrides.
Independent test criteria: Default precisions applied correctly (UG_M3/PPB→1, MG_M3/PPM→3); pollutant overrides take precedence; container types preserved.

- [x] T301 [US2] Implement round_for_reporting() function with registry lookup logic in src/air_quality/units.py
- [x] T302 [US2] Add pollutant override precedence logic (case-insensitive lookup) in src/air_quality/units.py
- [x] T303 [US2] Remove skip markers from tests/test_units_rounding.py (15 tests)
- [x] T304 [US2] Run pytest on test_units_rounding.py to verify all 15 tests pass
- [x] T305 [US2] Add documentation example to rounding policy registry showing override usage

## Phase 4 — Time Utilities Foundations (US3: Time Bounds for Metadata)

Goal: Implement ensure_timezone_aware(), to_utc(), compute_time_bounds() for UTC-aware time bounds with sub-second precision.
Independent test criteria: Naive datetimes get UTC tzinfo; tz-aware convert to UTC; bounds equal exact min/max from Polars with single collect; sub-second preserved.

- [X] T401 [US3] Implement ensure_timezone_aware() function in src/air_quality/time_utils.py handling naive/aware datetime
- [X] T402 [US3] Implement to_utc() function in src/air_quality/time_utils.py converting aware to UTC
- [X] T403 [US3] Implement compute_time_bounds() function using Polars agg(min,max) with single collect in src/air_quality/time_utils.py
- [X] T404 [US3] Add UTC conversion and precision preservation logic to compute_time_bounds in src/air_quality/time_utils.py
- [X] T405 [US3] Remove skip markers from tests/test_time_bounds.py (13 tests)
- [X] T406 [US3] Run pytest on test_time_bounds.py to verify all 13 tests pass
- [X] T407 [US3] Verify TimeBounds dataclass is frozen and slots are properly configured

## Phase 5 — Resampling Implementation (US4: Hourly Resampling)

Goal: Implement resample_mean() using pandas resample with immutability guarantee and numeric-only handling.
Independent test criteria: Returns new DataFrame; respects rule parameter; numeric columns only; original DataFrame unchanged; datetime coercion works.

- [X] T501 [US4] Implement resample_mean() function using pandas resample in src/air_quality/time_utils.py
- [X] T502 [US4] Add datetime column handling and numeric-only filtering to resample_mean in src/air_quality/time_utils.py
- [X] T503 [US4] Add immutability checks ensuring original DataFrame not mutated in src/air_quality/time_utils.py
- [X] T504 [US4] Remove skip markers from first 8 tests in tests/test_time_resample_roll.py (resample tests)
- [X] T505 [US4] Run pytest on TestResampleMean class to verify all 8 resample tests pass
- [X] T506 [US4] Add docstring example showing hourly resampling workflow
- [X] T507 [US4] ENHANCEMENT: Add optional `columns` parameter for selective column resampling
- [X] T508 [US4] ENHANCEMENT: Add 3 tests for column selection (specific columns, error handling, None default)
- [X] T509 [US4] ENHANCEMENT: Update contracts/time_utils_api.md with new signature

## Phase 6 — Rolling Window Implementation (US5: Rolling Mean QC Flagging)

Goal: Implement rolling_window_mean() with centered alignment, min_periods=1, and time-based sorting.
Independent test criteria: Window=1 equals original; centered alignment correct; sorts by time first; min_periods fills edges.

- [X] T601 [US5] Implement rolling_window_mean() function with sort-by-time logic in src/air_quality/time_utils.py
- [X] T602 [US5] Add centered rolling mean with min_periods=1 using pandas rolling in src/air_quality/time_utils.py
- [X] T603 [US5] Add numeric-only column filtering and immutability guarantee in src/air_quality/time_utils.py
- [X] T604 [US5] Remove skip markers from last 12 tests in tests/test_time_resample_roll.py (rolling tests)
- [X] T605 [US5] Run pytest on TestRollingWindowMean class to verify all 12 rolling tests pass
- [X] T606 [US5] Add docstring example showing QC spike detection workflow
- [X] T607 [US5] ENHANCEMENT: Add optional `columns` parameter for selective column smoothing
- [X] T608 [US5] ENHANCEMENT: Add 3 tests for column selection (specific columns, error handling, None default)
- [X] T609 [US5] ENHANCEMENT: Update contracts/time_utils_api.md with new signature

## Phase 7 — Schema Validation Implementation (US6: Multi-Column Unit Metadata)

Goal: Implement validate_units_schema() normalizing Unit|str to Unit with fail-fast error reporting including column context.
Independent test criteria: All-enum returns unchanged; all-string normalizes; mixed types work; invalid raises UnitError with column name; empty mapping handled.

- [X] T701 [US6] Implement validate_units_schema() function with Unit|str normalization in src/air_quality/units.py
- [X] T702 [US6] Add column-name error context to UnitError messages in validate_units_schema in src/air_quality/units.py
- [X] T703 [US6] Add immutability guarantee (returns new dict) in validate_units_schema in src/air_quality/units.py
- [X] T704 [US6] Remove skip markers from tests/test_units_schema_validation.py (15 tests)
- [X] T705 [US6] Run pytest on test_units_schema_validation.py to verify all 15 tests pass
- [X] T706 [US6] Update integration-notes.md with validated implementation patterns

## Phase 8 — Dataset Integration ✅

Goal: Integrate unit metadata validation into TimeSeriesDataset with column_units property.
Independent test criteria: Dataset construction validates units; property returns normalized mapping; invalid units raise UnitError with column name.

- [X] T801 Update TimeSeriesDataset.__init__ to accept column_units metadata in src/air_quality/dataset/time_series.py
- [X] T802 Add validate_units_schema call in dataset construction path in src/air_quality/dataset/time_series.py
- [X] T803 Add column_units property to TimeSeriesDataset in src/air_quality/dataset/time_series.py
- [X] T804 Create tests/test_dataset_units_integration.py with unit metadata validation tests (10 tests minimum)
- [X] T805 Run pytest on test_dataset_units_integration.py to verify all integration tests pass (12/12 ✅)
- [X] T806 Verify existing 18 dataset tests still pass (no regressions) (18/18 ✅)

## Phase 9 — Public API Exports ✅

Goal: Wire all implemented functions into public API via __init__.py exports.
Independent test criteria: All 11 functions + 1 Enum + 1 dataclass importable from air_quality; mypy clean; no circular imports.

- [X] T901 Uncomment and complete Unit/TimeBounds TYPE_CHECKING imports in src/air_quality/__init__.py
- [X] T902 Add public exports for all 6 units functions in src/air_quality/__init__.py
- [X] T903 Add public exports for all 5 time_utils functions in src/air_quality/__init__.py
- [X] T904 Add __all__ list with 13 exported names in src/air_quality/__init__.py
- [X] T905 Create tests/test_public_api.py verifying all imports work (13 import tests)
- [X] T906 Run pytest on test_public_api.py to verify all API tests pass (18/18 ✅)
- [X] T907 Run mypy on src/air_quality/__init__.py to verify no circular import issues (✅)

## Phase 10 — Performance Validation ✅

Goal: Verify O(n) vectorized performance targets and Constitution Sec 11 compliance.
Independent test criteria: 1M row conversion <50ms; single collect in compute_time_bounds; no Python row loops in any function.

- [X] T1001 Create tests/test_units_performance.py with 1M row conversion benchmark
- [X] T1002 Add compute_time_bounds single-collect verification test in tests/test_time_bounds.py
- [X] T1003 Run performance benchmarks and document results in HANDOFF.md
- [X] T1004 Verify no row-wise Python loops in any implemented function (code review)
- [X] T1005 Update requirements.md checklist with NFR-P01 and NFR-M01 verification

## Phase 11 — Documentation Polish ✅

Goal: Update all documentation to reflect completed implementation.
Independent test criteria: README examples work; quickstart.md reflects actual API; HANDOFF.md updated with final metrics.

- [x] T1101 Update README.md Feature 002 section with working code examples (replace stub note)
- [x] T1102 Update specs/002-units-time/quickstart.md with validated working examples
- [x] T1103 Update specs/002-units-time/HANDOFF.md with final test counts and performance results
- [x] T1104 Run markdown linter on all updated docs (skipped - not installed)
- [x] T1105 Verify all code examples in documentation actually execute successfully

## Phase 12 — Final Validation ✅

Goal: Complete all acceptance criteria and prepare for merge/release.
Independent test criteria: All 205 tests pass; mypy clean; requirements checklist 48/48; no regressions.

- [x] T1201 Run full test suite: verify 205 tests pass (73 existing + 132 new), 0 skipped
- [x] T1202 Run mypy on entire src/air_quality/ directory: verify 0 errors, 0 warnings (Feature 002 files clean)
- [x] T1203 Complete requirements.md checklist: verify all 48 items [x] verified
- [x] T1204 Update acceptance criteria AC2-AC6 in spec.md as satisfied
- [x] T1205 Run constitution compliance check against Sections 3, 7, 8, 9, 10, 11, 15
- [ ] T1206 Commit all changes not in just one commit but group similar files/changes in a commit. The commit message must be in conventional commit style.

---

## Dependencies (Implementation Order)

**Critical Path**:
1. US1 (Basic Unit Conversion) → US2 (Rounding) → US6 (Schema Validation)
   - US1 provides Unit.parse() which US6 needs
   - US2 uses Unit enum from US1
   - US6 calls Unit.parse() to normalize strings

2. US3 (Time Bounds) → US4 (Resampling) → US5 (Rolling Mean)
   - US3 provides time awareness utilities
   - US4 and US5 build on time column handling
   - Can be done in parallel with Units track after US3

3. Dataset Integration (Phase 8) requires:
   - US6 (validate_units_schema implemented)
   - US1 (Unit enum available)

**Parallel Opportunities**:
- After US1 complete: US2 and US3 can run in parallel
- After US3 complete: US4 and US5 can run in parallel
- After US6 complete: Dataset integration independent of US4/US5

**Recommended MVP Scope**: US1 + US3 (basic conversion + time bounds)

---

## Implementation Strategy

**Conversion from Stub to Implementation**:
1. Each phase implements functions that currently raise NotImplementedError
2. Remove skip markers from corresponding tests immediately after implementation
3. Tests MUST pass before proceeding to next phase
4. Run mypy after each phase to catch type regressions early

**Test-Driven Approach**:
- Tests already exist with full scenarios
- Implementation must satisfy existing test contracts
- Add edge case tests if discovered during implementation
- Maintain 100% pass rate (no skipped tests in implementation phase)

**Performance Discipline**:
- All implementations must use vectorized operations
- No Python row loops allowed (Constitution Sec 11)
- Single collect() in compute_time_bounds (Constitution Sec 11)
- Verify with performance tests in Phase 10

**Quality Gates Per Phase**:
✓ Implementation complete (NotImplementedError removed)
✓ Tests passing (skip markers removed, all green)
✓ Mypy clean (no new type errors)
✓ Documentation updated (docstrings with examples)
✓ No regressions (existing 73 tests still pass)

---

## Task Count Summary

- Phase 1 (Pre-Implementation): 4 tasks
- Phase 2 (US1 - Units Core): 8 tasks
- Phase 3 (US2 - Rounding): 5 tasks
- Phase 4 (US3 - Time Bounds): 7 tasks
- Phase 5 (US4 - Resampling): 9 tasks (6 original + 3 enhancements)
- Phase 6 (US5 - Rolling): 9 tasks (6 original + 3 enhancements)
- Phase 7 (US6 - Schema): 6 tasks
- Phase 8 (Dataset Integration): 6 tasks
- Phase 9 (Public API): 7 tasks
- Phase 10 (Performance): 5 tasks
- Phase 11 (Documentation): 5 tasks
- Phase 12 (Final Validation): 7 tasks

**Total**: 79 implementation tasks (73 original + 6 enhancements)

**Expected Outcome**: 160 passing tests (73 existing + 87 new), 0 skipped, mypy clean, all acceptance criteria satisfied.
