# Implementation Tasks: 001-core-foundation (AirQualityModule + Primitives)

**Status**: ✅ **COMPLETE** (All phases 0-10 finished)  
**Created**: 2025-11-08  
**Completed**: 2025-11-08  
**Feature Branch**: `001-core-foundation`  
**Test Results**: 73/73 passing  
**Version**: 0.1.0

## Scope Summary

Establish the foundational core: base module (`AirQualityModule`), column mapping utility, dataset abstractions backed by Polars LazyFrame, provenance + structured logging, standardized reporting, exceptions taxonomy, and a dummy exemplar module & tests. All tasks enforce constitution constraints (columnar-first, DRY, reproducibility, reporting schema).

## Legend

- Priority: P1 (must for feature), P2 (important), P3 (nice-to-have/adjacent)  
- Type: CODE / TEST / DOC / OPS / ARCH  
- Effort: XS (<15m), S (<1h), M (1–3h), L (3h+) 
- Dependencies: explicit prerequisite task IDs
- Acceptance: measurable completion criteria

## User Story Mapping

- US1 (Subclass & run): FR-001, FR-003, FR-004, FR-008, FR-009, FR-010
- US2 (Column mapping): FR-002, FR-007, FR-009
- US3 (Provenance & logging): FR-005, FR-006, FR-008, FR-009

## Tasks

### Phase 0: Repository Hygienics & Dependency Prep

- [X] ID: T0.1 | Priority: P1 | Type: ARCH | Effort: XS  
    Title: Confirm Python version alignment  
    Description: Ensure `pyproject.toml` Python constraint (>=3.12) matches design docs (spec assumed 3.11). Decide: proceed with 3.12 and note in docs.  
    Acceptance: Decision documented in `quickstart.md` NOTE block; no contradictory version statements.
- [X] ID: T0.2 | Priority: P1 | Type: CODE | Effort: XS  
    Title: Add minimal runtime deps  
    Description: Add Polars, pyarrow, pandas to `project.dependencies` (pin conservative minor ranges).  
    Acceptance: `pyproject.toml` updated; lock resolved; import succeeds in a scratch snippet.
- [X] ID: T0.3 | Priority: P1 | Type: TEST | Effort: XS  
    Title: Dependency smoke test  
    Description: Create `tests/test_deps_import.py` verifying imports (polars.lazy, pyarrow.Table, pandas.DataFrame).  
    Acceptance: Test passes.
- [X] ID: T0.4 | Priority: P1 | Type: OPS | Effort: XS  
    Title: Create/verify ignore files  
    Description: Detect git repo and create/update `.gitignore` with Python/IDE/OS patterns; verify presence.  
    Acceptance: `.gitignore` exists with essential patterns.

### Phase 1: Exceptions & Error Taxonomy

- [X] ID: T1.1 | Priority: P1 | Type: CODE | Effort: XS  
    Title: Implement core exceptions  
    Path: `src/air_quality/exceptions.py`  
    Description: Define SchemaError, DataValidationError, UnitError, AlgorithmConvergenceError, ConfigurationError, PerformanceWarning (subclass Warning).  
    Acceptance: Classes defined; docstrings specifying usage; imported by other modules without circularity.
- [X] ID: T1.2 | Priority: P1 | Type: TEST | Effort: XS  
    Title: Exception raising tests  
    Path: `tests/test_exceptions.py`  
    Description: Assert raising each custom exception; PerformanceWarning emitted via warnings module.  
    Acceptance: All tests green.

### Phase 2: Structured Logging Utility

- [X] ID: T2.1 | Priority: P1 | Type: CODE | Effort: S  
    Title: Logging helper  
    Path: `src/air_quality/logging.py`  
    Description: Provide `get_logger(name: str, **context)` returning a logger with structured extra fields and a consistent formatter including timestamp, level, module, message. Use lazy formatting.  
    Acceptance: Logger emits expected format in a test capture.
- [X] ID: T2.2 | Priority: P2 | Type: TEST | Effort: S  
    Title: Logging format test  
    Path: `tests/test_logging.py`  
    Description: Capture log output for start/finish events; verify regex for expected fields.  
    Acceptance: Test passes; no extraneous handlers duplication.

### Phase 3: Provenance Facility

- [X] ID: T3.1 | Priority: P1 | Type: CODE | Effort: S  
    Title: Provenance record dataclass  
    Path: `src/air_quality/provenance.py`  
    Description: Implement `ProvenanceRecord` (module_name, domain, dataset_id|None, config_hash, run_timestamp, version). Provide `make_provenance(module, dataset, config)` helper computing hash (stable JSON canonicalization) and timestamp (UTC ISO).  
    Acceptance: Dataclass serializes to dict; helper returns consistent hash for same config ordering.
- [X] ID: T3.2 | Priority: P1 | Type: TEST | Effort: XS  
    Title: Provenance determinism test  
    Path: `tests/test_provenance.py`  
    Description: Same config dict with different key order yields same hash; timestamp is ISO 8601; version matches `air_quality.__version__`.  
    Acceptance: Test passes.

### Phase 4: Column Mapping Utility

- [X] ID: T4.1 | Priority: P1 | Type: CODE | Effort: M  
    Title: Column mapping core  
    Path: `src/air_quality/mapping.py`  
    Description: Implement `ColumnMapper` with method `map(df, required, synonyms)` performing: (a) explicit mapping if provided; (b) fuzzy/synonym resolution (unique matches); (c) raise SchemaError for missing/ambiguous. Return `ColumnMappingResult` containing canonical mapping dict, diagnostics list, and resolved columns list. Avoid row operations.  
    Acceptance: Handles explicit mapping, synonym mapping, ambiguous error with candidate list, missing error with list of unresolved required.
- [X] ID: T4.2 | Priority: P1 | Type: TEST | Effort: M  
    Title: Mapping behavior tests  
    Path: `tests/test_mapping.py`  
    Description: Cases: explicit mapping; synonym mapping success; ambiguous (two similar columns) error; missing required column error; large synthetic DataFrame performance smoke (no row loops).  
    Acceptance: All cases pass; performance smoke asserts mapping time under threshold (e.g., <0.5s for 1e6 rows minimal columns). (Note: may mark performance test as XFAIL if environment constrained.)
- [X] ID: T4.3 | Priority: P2 | Type: CODE | Effort: S  
    Title: Mapping diagnostics enrichment  
    Path: `src/air_quality/mapping.py`  
    Description: Add optional flag to include candidate suggestions for unresolved fields.  
    Acceptance: Diagnostics list contains structured suggestion entries.

### Phase 5: Dataset Abstractions (Polars LazyFrame)

- [X] ID: T5.1 | Priority: P1 | Type: CODE | Effort: M  
    Title: BaseDataset abstract class  
    Path: `src/air_quality/dataset/base.py`  
    Description: Define abstract interface: `.from_dataframe(df, mapping_result)` → instance storing Polars LazyFrame; properties: `.lazyframe`, `.schema`, `.metadata` (including mapping); conversions: `.to_arrow()`, `.to_pandas()`. Validate non-empty.  
    Acceptance: Instantiation works; empty DataFrame raises DataValidationError.
- [X] ID: T5.2 | Priority: P1 | Type: CODE | Effort: M  
    Title: TimeSeriesDataset concrete implementation  
    Path: `src/air_quality/dataset/time_series.py`  
    Description: Subclass BaseDataset; enforce presence of a time index canonical field; add `.time_index_name` property.  
    Acceptance: Construction requires time field; error if absent.
- [X] ID: T5.3 | Priority: P1 | Type: TEST | Effort: M  
    Title: Dataset construction tests  
    Path: `tests/test_dataset.py`  
    Description: Validate base/time-series construction, conversions to Arrow/pandas retain schema & mapping metadata, error on empty input, error on missing time index.  
    Acceptance: All tests pass.
- [X] ID: T5.4 | Priority: P2 | Type: TEST | Effort: S  
    Title: LazyFrame internal test  
    Path: `tests/test_dataset_lazyframe.py`  
    Description: Ensure internal storage is LazyFrame; operations chained remain lazy (verify plan length >0).  
    Acceptance: Test passes.

### Phase 6: Base Analysis Module

- [X] ID: T6.1 | Priority: P1 | Type: CODE | Effort: M  
    Title: Implement `AirQualityModule` base class  
    Path: `src/air_quality/module.py`  
    Description: Template-method pattern with lifecycle: `__init__(dataset, config)`, protected hooks `_validate_inputs()`, `_run_impl()`, `_post_process()`. Public: `run(operations: Optional[Sequence[Enum]] = None)`, `report_dashboard()`, `report_cli()`. Use enums for specifying which operations to execute (modules define their own operation enums). Attach provenance via helper; store results dict; include mapping summary in CLI.  
    Acceptance: Class imports; `run()` enforces single execution idempotence; missing dataset raises error; enum-based operation selection works.
- [X] ID: T6.2 | Priority: P1 | Type: CODE | Effort: S  
    Title: Dummy `RowCountModule` implementation  
    Path: `src/air_quality/modules/row_count.py`  
    Description: Subclass `AirQualityModule`; `_run_impl()` counts rows; `_post_process()` adds simple QC flag if zero rows (should never pass earlier validation). Define RowCountOperation enum if module has multiple operations.  
    Acceptance: RowCountModule run returns metrics with `row_count` >0 for valid dataset.
- [X] ID: T6.3 | Priority: P1 | Type: TEST | Effort: M  
    Title: Module lifecycle tests  
    Path: `tests/test_module_lifecycle.py`  
    Description: Run dummy module; assert dashboard keys (module, domain, schema_version, metrics, provenance). CLI output contains mapping summary & metrics. Second `run()` call either no-op or raises controlled error (choose design).  
    Acceptance: All assertions pass.
- [X] ID: T6.4 | Priority: P2 | Type: TEST | Effort: S  
    Title: Logging integration test  
    Path: `tests/test_module_logging.py`  
    Description: Capture logs during module `run()`; verify start/finish and elapsed time are present.  
    Acceptance: Test passes.

### Phase 7: Reporting & Formatting

- [X] ID: T7.1 | Priority: P1 | Type: CODE | Effort: S  
    Title: Dashboard schema type definition  
    Path: `src/air_quality/module.py`  
    Description: Add DashboardPayload TypedDict for IDE type hints. Reporting assembly is already implemented in AirQualityModule.report_dashboard() - no separate helper needed (DRY compliance).  
    Acceptance: Type hint available; base module enforces schema.
- [X] ID: T7.2 | Priority: P1 | Type: TEST | Effort: XS  
    Title: Reporting integrity test  
    Path: `tests/test_module_lifecycle.py`  
    Description: Reporting validation already covered in lifecycle tests (test_dashboard_report_structure, test_cli_report_content, etc.).  
    Acceptance: Tests pass; dashboard/CLI schemas validated.

### Phase 8: Performance & DRY Assurance

- [X] ID: T8.1 | Priority: P2 | Type: TEST | Effort: M  
    Title: No unnecessary DataFrame copies  
    Path: `tests/test_performance_copy.py`  
    Description: Use memory introspection or id() checks to ensure conversions only happen when requested; base `run()` doesn't clone dataset.  
    Acceptance: Test passes or documented limitation.
- [X] ID: T8.2 | Priority: P3 | Type: TEST | Effort: M  
    Title: Large dataset mapping timing benchmark  
    Path: `tests/test_mapping_perf.py`  
    Description: Synthetic large DF (1e6 rows) run mapping; assert runtime within threshold or mark XFAIL with rationale.  
    Acceptance: Perf metrics logged; threshold outcome recorded.

### Phase 9: Documentation & README Updates

- [X] ID: T9.1 | Priority: P1 | Type: DOC | Effort: S  
    Title: Update `quickstart.md` with Python 3.12 note & dataset construction example using mapping  
    Acceptance: Quickstart shows mapping -> dataset -> module run sequence.
- [X] ID: T9.2 | Priority: P1 | Type: DOC | Effort: S  
    Title: README enhancement  
    Path: `README.md`  
    Description: Add installation, brief architecture, example RowCountModule usage, and provenance rationale.  
    Acceptance: Sections added; lint passes.
- [X] ID: T9.3 | Priority: P2 | Type: DOC | Effort: XS  
    Title: Add CHANGELOG entry (0.1.0 foundation)  
    Path: `CHANGELOG.md`  
    Description: Create if missing; summarize foundational core.  
    Acceptance: File exists; version entry present.

### Phase 10: Quality Gates & Finalization

- [X] ID: T10.1 | Priority: P1 | Type: OPS | Effort: XS  
    Title: Run full test suite  
    Acceptance: All tests green; performance XFAIL documented.
- [X] ID: T10.2 | Priority: P1 | Type: OPS | Effort: XS  
    Title: Lint & type check (mypy configured)  
    Description: mypy configured with pandas-stubs and pyarrow-stubs; all type checks passing.  
    Acceptance: No syntax errors; type check passing on 11 source files.
- [X] ID: T10.3 | Priority: P2 | Type: OPS | Effort: XS  
    Title: Version bump decision  
    Description: Confirm that initial implementation retains 0.1.0; note semantic version policy in README.  
    Acceptance: README includes versioning note.

## Parallelization Notes

- Phases 1–3 (exceptions, logging, provenance) can proceed in parallel after deps added.
- Mapping (Phase 4) precedes dataset (Phase 5) because dataset needs mapping result structure.
- Base module (Phase 6) depends on dataset + provenance + logging + reporting helper.
- Performance tests (Phase 8) depend on mapping & dataset.


## Risk & Mitigation

- Polars LazyFrame API changes: Pin minor version and add CI reminder comment.  
- Performance variability on local machine: Mark perf tests XFAIL with rationale if threshold unreachable.  
- Logging handler duplication: Ensure helper checks existing handlers.


## Completion Checklist (Roll-Up)

- [X] All P1 tasks complete
- [X] Dummy module run example works end-to-end
- [X] Tests green (excluding documented XFAILs)
- [X] README & quickstart updated
- [X] Versioning and provenance documented


## Acceptance Summary

Feature considered complete when RowCountModule can ingest a pandas DataFrame via mapping → TimeSeriesDataset → run → produce dashboard + CLI report with provenance and structured logs, all while meeting error behaviors and performance discipline.
