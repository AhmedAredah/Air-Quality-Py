# Feature Specification: Foundational Core (AirQualityModule + Primitives)

**Feature Branch**: `001-core-foundation`  
**Created**: 2025-11-08  
**Status**: Draft  
**Input**: User description: "Design and implement the foundational core for the air_quality library: AirQualityModule base class and minimal supporting utilities (datasets, column mapping, exceptions, provenance, logging), compliant with the constitution and optimized for large columnar datasets."

## User Scenarios & Testing (mandatory)

### User Story 1 - Subclass and run a module (Priority: P1)

As a module developer, I can subclass the base analysis module, provide minimal hooks, and execute a run that validates inputs, performs core logic, and produces standard reports.

**Why this priority**: Enables all future domain modules (PMF, AQI, EJ). Establishes the single inheritance and reporting pattern mandated by the constitution.

**Independent Test**: Using a simple time-series dataset, create a dummy subclass that computes row count and returns a dashboard payload and CLI text without modifying the core.

**Acceptance Scenarios**:

1. Given a canonicalized dataset and config, When `run()` is invoked, Then `results` contains at least one metric and `provenance` is attached.
2. Given a completed run, When `report_dashboard()` is invoked, Then it returns a dict with module, domain, schema_version, metrics, and provenance keys.
3. Given a completed run, When `report_cli()` is invoked, Then it returns a human-readable summary including inputs, methods, and key results.

---

### User Story 2 - Map user data to canonical schema (Priority: P1)

As a data integrator, I can map arbitrary input columns into the canonical schema using an explicit mapping or safe fuzzy matching, and receive clear errors for missing or ambiguous fields.

**Why this priority**: Guarantees consistent, DRY ingestion across all modules and prevents silent misinterpretation of user data.

**Independent Test**: Provide DataFrames with (a) perfect explicit mappings, (b) synonym-based columns, (c) ambiguous columns, and (d) missing required columns; verify success and error behaviors.

**Acceptance Scenarios**:

1. Given an explicit mapping dict, When mapping runs, Then all required canonical fields are resolved exactly and recorded in mapping metadata.
2. Given only synonyms, When mapping runs, Then unique candidates are resolved; ambiguous or missing fields raise a schema/validation error with candidate listings.
3. Given successful mapping, When constructing a dataset, Then internal storage is columnar and original-to-canonical mapping is preserved in metadata.

---

### User Story 3 - Provenance and structured logging (Priority: P2)

As a maintainer, I can see structured logs during runs and a provenance record on outputs, including dataset identifier, config hash, timestamps, and software version.

**Why this priority**: Essential for reproducibility, audit, and compliance; ensures traceability from day one.

**Independent Test**: Execute a run and verify that logs include module name and timing, and that the dashboard output contains provenance fields.

**Acceptance Scenarios**:

1. Given a module run, When inspecting logs, Then entries include timestamps, module name, level, and messages for start/finish and key events.
2. Given a completed run, When inspecting `provenance`, Then it includes `module_name`, `domain`, `dataset_id` (if available), `config_hash`, and `run_timestamp`.

### Edge Cases

- Empty dataset input: constructing a module or calling `run()` fails with a clear validation error.
- Ambiguous mapping: multiple candidate columns for a canonical field produces a descriptive error listing candidates and next steps.
- Missing required columns: mapping halts with a clear error showing missing fields and synonyms tried.
- Large DataFrames (millions of rows): mapping performs vectorized operations; no row-wise loops in critical paths.

## Requirements (mandatory)

### Functional Requirements

- FR-001: Provide a single root base class for analysis modules that enforces the lifecycle (`run`, `report_dashboard`, `report_cli`) and template-method hooks.
- FR-002: Provide a centralized column-mapping utility implementing explicit mapping → safe fuzzy mapping → strict schema validation, returning mapping diagnostics.
- FR-003: Provide an abstract dataset base that wraps columnar data as the primary representation and exposes minimal inspection utilities.
- FR-004: Provide at least one concrete dataset type for time series that stores data internally in a columnar format even when constructed from row-oriented inputs.
- FR-005: Provide a provenance record structure and helper to attach audit metadata to outputs.
- FR-006: Provide a structured logging helper returning a configured logger usable with extra context fields.
- FR-007: Disallow silent imputation, silent mapping guesses, or silent failure; all such behaviors must either be explicit or error.
- FR-008: Ensure reporting methods return the standardized dashboard structure and a complete CLI text with inputs, methods, results, and QC/caveats sections.
- FR-009: Ensure minimal performance discipline: no unnecessary copies in base lifecycle; mapping operations vectorized; columnar-first data handling.
- FR-009: Ensure minimal performance discipline: no unnecessary copies in base lifecycle; mapping operations vectorized; columnar-first data handling.
- FR-010: Internal dataset storage MUST use Polars LazyFrame for time series (lazy columnar execution); provide helper methods for explicit conversion to PyArrow Table (preferred interchange) and pandas DataFrame without altering canonical metadata.

### Key Entities (include if feature involves data)

- AirQualityModule: Base analysis class implementing lifecycle and reporting entrypoints.
- BaseDataset: Abstract base for canonical dataset objects with columnar storage and metadata.
- TimeSeriesDataset: Concrete dataset for time-indexed observations using columnar storage.
- TimeSeriesDataset: Concrete dataset for time-indexed observations using Polars LazyFrame internally; exposes `.to_arrow()` and `.to_pandas()` for boundary conversions while retaining canonical mapping metadata.
- ColumnMapper: Centralized three-level mapper; ColumnMappingResult: mapping outcome and diagnostics.
- ProvenanceRecord: Serializable record capturing run metadata for audit and traceability.
- Exceptions: SchemaError/DataValidationError, UnitError, AlgorithmConvergenceError, ConfigurationError, PerformanceWarning.

## Success Criteria (mandatory)

### Measurable Outcomes

- SC-001: A dummy subclass built on this core executes `run()` and produces non-empty dashboard and CLI reports without modifying the base.
- SC-002: Column mapping resolves explicit and unique synonym cases and raises clear errors for missing/ambiguous fields.
- SC-003: Dataset internals are columnar by default; constructing from a row-oriented input still yields columnar storage.
- SC-004: Provenance dictionaries include timestamp, module/domain, and a stable configuration identifier for simple configs.
- SC-005: Logs emitted during `run()` include start/end markers with elapsed time and module context.

## Clarifications

### Session 2025-11-08

- Q: Internal columnar backend strategy? → A: Adopt Polars LazyFrame internally with conversion helpers to PyArrow Table (interchange) and pandas DataFrame at boundaries.

### Applied Changes

Added FR-010 and updated TimeSeriesDataset entity to define Polars LazyFrame core; ensures constitution columnar-first mandate while enabling lazy optimization. Conversion helpers will not duplicate data unnecessarily and will preserve canonical mapping metadata.

## Constitution Constraints (mandatory)

1. Inheritance & Interface: All modules MUST inherit `AirQualityModule` and use `from_dataframe` / `from_dataset` / `run` / `report_dashboard` / `report_cli` with required hooks.
2. Column Mapping: All tabular inputs MUST be canonicalized through the centralized three-level mapping utility; no ad-hoc mapping logic in modules.
3. Units & Provenance: Core exposes provenance attachment; units registry hooks are reserved for future work but must not be hard-coded in this core.
4. Performance & Scalability: Internal data structures are columnar-first; operations are vectorized; base lifecycle avoids unnecessary copies; large datasets are the default design case.
5. Reporting: Dashboard payload includes `module`, `domain`, `schema_version`, metrics, flags, and provenance; CLI text surfaces warnings/QC and mapping summary.
6. Testing & Benchmarks: Acceptance tests cover mapping success/failure and basic run/report; future performance regression testing is planned.
7. EJ/Health/Ethics: No domain metrics yet; foundation ensures reporting surfaces flags and supports later EJ/health modules without bypassing safeguards.
8. DRY & Shared Utilities: Mapping, logging, provenance, and base lifecycle implemented once in shared modules; duplication in future modules is prohibited.
9. Security & Privacy: Logs and errors avoid emitting raw sensitive data; mapping/provenance store only necessary metadata.
10. Versioning Impact: Introducing the base and primitives is additive; future schema/result changes to core reporting will trigger MINOR or MAJOR bumps per constitution.

## Constitution Constraints *(mandatory)*

Document how this feature complies with core invariants. If any item does not apply, state "N/A" with rationale.

1. Inheritance & Interface: Confirms all new analysis modules inherit `AirQualityModule` and implement required hooks.
2. Column Mapping: Lists required canonical fields + explicit mapping strategy + ambiguity handling plan.
3. Units & Provenance: Specifies units registry interactions, conversion rules, provenance fields, RNG seed plan.
4. Performance & Scalability: Details columnar backend usage (PyArrow/Polars), vectorization, memory strategy, chunking, benchmarks to run.
5. Reporting: Defines dashboard schema additions and CLI sections; includes uncertainty exposure.
6. Testing & Benchmarks: Enumerates regression tests, coverage targets, performance guardrails, validation CLI invocation.
7. EJ/Health/Ethics: States any disparity metrics or privacy safeguards, threshold definitions, fairness checks for ML components.
8. DRY & Shared Utilities: Identifies reused utilities (aggregation, units, QC, logging) and confirms no duplicated logic.
9. Security & Privacy: Specifies handling of sensitive fields, anonymization thresholds, credential management.
10. Versioning Impact: Notes if changes affect scientific results or schemas (triggering MINOR/MAJOR bump) and migration plan.
