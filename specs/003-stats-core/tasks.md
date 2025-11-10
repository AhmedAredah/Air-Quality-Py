---

description: "Tasks for Feature 003 – Core Statistical Analysis"
---

# Tasks: Feature 003 – Core Statistical Analysis (Descriptive, Correlation, Trends)

**Input**: Design documents in `specs/003-stats-core/` (spec.md, plan.md, research.md, data-model.md, contracts/python_api.md, quickstart.md)
**Prerequisites**: plan.md & spec.md (present)
**Tests**: Included (unit, integration, perf smoke) because spec defines measurable success criteria and performance targets.

## Format: `[ID] [P?] [Story] Description`

- **[P]** task can run in parallel (different files, no dependency ordering conflicts)
- **[Story]** label required for user story phases (US1, US2, US3)

## Phase 1: Setup (Shared Infrastructure)

Purpose: Ensure baseline environment & tooling (some already exist; tasks verify or extend as needed).

- [X] T001 Verify existing `AirQualityModule` interface completeness against Constitution (no code change) in `src/air_quality/module.py`
- [X] T002 ~~Add stats_analysis package init~~ → Created `src/air_quality/analysis/__init__.py` (primitives package)
- [X] T003 [P] ~~Create core package directory tree~~ → Created `src/air_quality/analysis/` (renamed from stats_analysis/core)
- [X] T004 [P] Add primitive placeholder files: `descriptive.py`, `correlation.py`, `trend.py` in `src/air_quality/analysis/`
- [X] T005 Add module orchestrator stubs in `src/air_quality/modules/statistics/` (descriptive.py, correlation.py, trend.py)
- [X] T006 Configure mypy strict settings for new package if required in `pyproject.toml`
- [X] T007 Ensure test folder scaffolding: `tests/unit/statistics/`, `tests/integration/modules/`, `tests/perf_smoke/`

---

## Phase 2: Foundational (Blocking Prerequisites)

Purpose: Shared logic & utilities required across all stories.

- [X] T008 ~~Implement shared flag filtering helper in `src/air_quality/stats_analysis/core/common.py`~~ (MOVED: QC filtering functions moved to library-level `src/air_quality/qc_flags.py`, common.py deleted)
- [X] T009 [P] ~~Implement numeric column validation helper in `src/air_quality/stats_analysis/core/validation.py`~~ (REMOVED: Redundant with BaseDataset/TimeSeriesDataset validation. Stats modules validate inline using Polars expressions)
- [X] T010 [P] Implement helper to compute quantiles list (5,25,75,95) in `src/air_quality/analysis/descriptive.py` (placeholder returning list)
- [X] T011 ~~Implement provenance attachment helper wrapper~~ (REMOVED: Use library-level `src/air_quality/provenance.py` instead with Enum-based make_provenance())
- [X] T012 [P] ~~Add config dataclasses~~ → Add config enums inline in each module file: `DescriptiveStatsConfig`, `CorrelationConfig`, `TrendConfig` in `src/air_quality/modules/statistics/{descriptive,correlation,trend}.py`
- [X] T013 ~~Integrate time bounds retrieval via `time_utils.compute_time_bounds`~~ (N/A: Use library-level provenance.py with make_provenance())
- [X] T014 Add constants (enum-based TimeUnit, CorrelationMethod, StatisticType) in `src/air_quality/analysis/constants.py`
- [X] T015 [P] ~~Add unit presence checking utility~~ (REMOVED: Incorrect design - checked pollutant names instead of column names. Unit validation handled by `TimeSeriesDataset.column_units` property)
- [X] T016 Add error mapping docstrings referencing Constitution sections in each new helper
- [X] T017 Create initial perf synthetic dataset factory in `tests/perf_smoke/factories.py`
- [X] T018 [P] Add test utilities for random reproducible dataset generation in `tests/unit/statistics/utils.py`

Checkpoint: All foundational helpers & configs in place.

**Architecture Notes:**
- Primitives package: `src/air_quality/analysis/` (computational functions, constants)
- Module implementations: `src/air_quality/modules/statistics/` (DescriptiveStatsModule, CorrelationModule, TrendModule)
- Library-level utilities: `qc_flags.py`, `provenance.py`, `units.py`, `time_utils.py`
- Config enums: Defined inline in each module file (better cohesion)
- No `stats_analysis` package (renamed to `analysis` to avoid stdlib conflict)

---

## Phase 3: User Story 1 – Descriptive summaries per site/pollutant (Priority: P1) 🎯 MVP (US1)

Goal: Provide descriptive statistics per pollutant and grouping keys with QC-aware counts.
Independent Test: Run `DescriptiveStatsModule` on small canonical long dataset and assert tidy output rows for each stat with correct counts.

### Tests (write first)
- [ ] T019 [P] [US1] Unit test: basic single-site stats in `tests/unit/statistics/test_descriptive_basic.py`
- [ ] T020 [P] [US1] Unit test: grouping by site_id multi-pollutant in `tests/unit/statistics/test_descriptive_grouped.py`
- [ ] T021 [P] [US1] Unit test: flag filtering & counts in `tests/unit/statistics/test_descriptive_flags.py`
- [ ] T022 [US1] Integration test module CLI report in `tests/integration/modules/test_descriptive_module_cli.py`

### Implementation
- [ ] T023 Implement quantile/stat aggregation logic in `src/air_quality/analysis/descriptive.py`
- [ ] T024 [P] Implement descriptive primitive function `compute_descriptives` (Polars) in same file
- [ ] T025 [P] Implement fallback Pandas path (if needed) in same file with explanatory docstring
- [ ] T026 Implement `DescriptiveStatsModule` `_run_impl` in `src/air_quality/modules/statistics/descriptive.py`
- [ ] T027 Implement dashboard report builder in same module file
- [ ] T028 Implement CLI report builder in same module file
- [ ] T029 Add provenance fields (stats list, grouping, n_total/valid/missing schema) using `make_provenance()` from `src/air_quality/provenance.py`
- [ ] T030 [P] Add mypy type hints & pass mypy for descriptive code
- [ ] T031 Add docs example cross-link in `quickstart.md` referencing new module

Checkpoint: US1 independently functional & testable.

---

## Phase 4: User Story 2 – Correlations across pollutants (Priority: P2) (US2)

Goal: Provide pairwise Pearson/Spearman correlations with ordered unique pairs, per group optional.
Independent Test: Run on canonical dataset; verify diagonal + ordered pairs, correct n, grouping behavior.

### Tests (write first)
- [ ] T032 [P] [US2] Unit test: pearson two pollutants global in `tests/unit/statistics/test_correlation_basic.py`
- [ ] T033 [P] [US2] Unit test: spearman ranking check in `tests/unit/statistics/test_correlation_spearman.py`
- [ ] T034 [P] [US2] Unit test: grouping by site & pair ordering in `tests/unit/statistics/test_correlation_grouped.py`
- [ ] T035 [US2] Unit test: missing units error & override flag in `tests/unit/statistics/test_correlation_units.py`
- [ ] T036 [US2] Integration test CLI & dashboard payload in `tests/integration/modules/test_correlation_module_cli.py`

### Implementation
- [ ] T037 Implement correlation primitive core (pearson) in `src/air_quality/analysis/correlation.py`
- [ ] T038 [P] Implement spearman rank transform + correlation in same file
- [ ] T039 [P] Implement ordered pair generation (var_x <= var_y) utility in same file
- [ ] T040 Implement `CorrelationModule` `_run_impl` in `src/air_quality/modules/statistics/correlation.py`
- [ ] T041 Implement dashboard report builder in same module file
- [ ] T042 Implement CLI report builder with override warning logic
- [ ] T043 [P] Integrate unit override provenance fields (units_status, missing list) using `make_provenance()` from `src/air_quality/provenance.py`
- [ ] T044 Add mypy types & fix any typing issues for correlation code
- [ ] T045 Add performance smoke test (100k x 4 pollutants) in `tests/perf_smoke/test_perf_correlation.py`

Checkpoint: US2 independently functional.

---

## Phase 5: User Story 3 – Simple linear trends over time (Priority: P3) (US3)

Goal: Provide linear trends (slope/intercept) with calendar-aware time units and duration/min_samples flags.
Independent Test: Known linear slope dataset returns expected slope within tolerance; short duration flagged.

### Tests (write first)
- [ ] T046 [P] [US3] Unit test: day time_unit linear slope in `tests/unit/statistics/test_trend_basic.py`
- [ ] T047 [P] [US3] Unit test: calendar_year fractional computation in `tests/unit/statistics/test_trend_calendar_year.py`
- [ ] T048 [P] [US3] Unit test: min_duration_years short flag in `tests/unit/statistics/test_trend_short_duration.py`
- [ ] T049 [US3] Unit test: unit presence enforcement in `tests/unit/statistics/test_trend_units.py`
- [ ] T050 [US3] Integration test CLI report with flags in `tests/integration/modules/test_trend_module_cli.py`

### Implementation
- [ ] T051 Use `compute_elapsed_time()` from `src/air_quality/units.py` for calendar-aware time conversion
- [ ] T052 [P] Implement closed-form OLS slope/intercept primitive in `src/air_quality/analysis/trend.py`
- [ ] T053 [P] Implement duration & short_duration_flag logic in same file
- [ ] T054 Implement `TrendModule` `_run_impl` in `src/air_quality/modules/statistics/trend.py`
- [ ] T055 Implement dashboard report builder in same module file
- [ ] T056 Implement CLI report builder including short_duration & low_n flags
- [ ] T057 [P] Integrate units enforcement & provenance (time bounds, duration, thresholds) using `make_provenance()` from `src/air_quality/provenance.py`
- [ ] T058 Add performance smoke test (100k rows) in `tests/perf_smoke/test_perf_trend.py`
- [ ] T059 Type hints & mypy pass for trend code

Checkpoint: US3 independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T060 [P] Add combined perf smoke for all primitives in `tests/perf_smoke/test_perf_all.py`
- [ ] T061 Documentation: augment `quickstart.md` with correlation & trend examples
- [ ] T062 Add README section summarizing Feature 003 capabilities
- [ ] T063 [P] Refactor any duplicated helper logic across primitives in `src/air_quality/analysis/`
- [ ] T064 Add reproducibility manifest example for stats run in `docs/` (if docs dir exists)
- [ ] T065 Update `CHANGELOG.md` with Feature 003 entry (MINOR bump)
- [ ] T066 [P] Review all module files (`src/air_quality/modules/statistics/`) for code quality and consistency
- [ ] T067 Verify all config enums follow inline pattern (DescriptiveStatsConfig, CorrelationConfig, TrendConfig)
- [ ] T068 Final type checking pass: `mypy src/air_quality/analysis/ src/air_quality/modules/statistics/` with strict mode

---

## Dependencies & Execution Order

Phase order: 1 → 2 → (3,4,5 parallel after 2) → 6.

User story independence: US1 is MVP; US2 & US3 depend only on foundational phase; no hard dependency on US1 outputs (correlation/trend operate on canonical dataset directly).

Within stories: Tests precede implementation; parallel [P] tasks can execute simultaneously across distinct files.

## Parallel Opportunities

- Setup: T002–T005 in parallel after T001
- Foundational: T009, T010, T012, T015, T018 parallel (enums, constants, test utilities)
- US1: T019–T021 tests parallel; T024 & T025 parallel (primitives in `analysis/descriptive.py`); T027 & T028 parallel (reports in module)
- US2: T032–T035 tests parallel; T038 & T039 parallel (primitives in `analysis/correlation.py`)
- US3: T046–T048 tests parallel; T052 & T053 parallel (primitives in `analysis/trend.py`)
- Polish: T060, T066, T068 parallel (combined perf tests, code review, type checking)

## Implementation Strategy

1. Deliver MVP with US1 (descriptive) for early feedback - uses primitives from `analysis/` and module from `modules/statistics/`
2. Layer in correlations (US2) focusing on correctness & performance
3. Add trends (US3) with calendar-aware logic using `compute_elapsed_time()` from `units.py`
4. Polish phase consolidates perf, docs, reproducibility manifest, and changelog

## Task Counts

- Total tasks: 68
- US1 tasks (tests + impl + provenance): 13 (T019–T031)
- US2 tasks: 14 (T032–T045)
- US3 tasks: 14 (T046–T059)
- Foundational & setup: 18 (T001–T018)
- Polish: 9 (T060–T068)

## Independent Test Criteria Summary

- US1: Tidy stats table, correct counts, flag exclusion verification.
- US2: Ordered pairs unique, diagonal present, correct n, override provenance path.
- US3: Accurate slopes within tolerance, duration & low_n flags, unit enforcement.

## MVP Scope

MVP = Phases 1–3 (through T031). Provides immediate value (descriptive stats) reused by downstream features.

## Format Validation

All tasks follow: `- [ ] T### [P]? [USn]? Description with file path`.
