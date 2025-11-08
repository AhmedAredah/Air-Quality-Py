# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [single/web/mobile - determines source structure]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The following MUST be explicitly addressed and linked to the design/spec:

- Data schema & mapping: uses centralized three-level column-mapping utility; required canonical fields identified; mapping plan for user inputs; no ad-hoc mapping.
- Architecture: module(s) inherit from `AirQualityModule` and provide `from_dataframe`/`from_dataset`/`run`/`report_dashboard`/`report_cli` with required hooks.
- Performance: large-dataset plan (columnar I/O with Arrow/Parquet; vectorized operations; chunking/streaming if needed; no Python row loops in critical paths).
- Units & provenance: central units registry usage; provenance fields to be attached by `run()`; RNG seed strategy if stochastic.
- Reporting: dashboard schema_version and CLI content (inputs, methods, key results, QC/caveats, mapping summary).
- Testing/benchmarks: regression tests for numerics; coverage targets; performance baseline/guardrails; validation/doctor CLI coverage.
- EJ/health/ethics: disparity metrics or safeguards as applicable; privacy/aggregation rules if sensitive data.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code Layout
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
````markdown
# Implementation Plan: Foundational Core (AirQualityModule + Primitives)

**Branch**: `001-core-foundation` | **Date**: 2025-11-08 | **Spec**: ../spec.md
**Input**: Feature specification from `/specs/001-core-foundation/spec.md`

**Note**: This plan follows the project constitution and planning workflow.

## Summary

Establish a small but robust foundation for `air_quality`:
- Implement `AirQualityModule` as the single root template-method base.
- Provide minimal primitives: exceptions, structured logging, provenance helper, dataset abstraction with `TimeSeriesDataset`, and centralized three-level column mapper.
- Internal data model is columnar-first using Polars LazyFrame with explicit conversion helpers to PyArrow Table (interchange) and pandas at boundaries.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: polars (LazyFrame), pyarrow (Table/Parquet), pandas (interop), typing-extensions (if needed)  
**Storage**: Parquet/Arrow (columnar); no DB in scope  
**Testing**: pytest, pytest-cov  
**Target Platform**: Windows/Linux/macOS (CPython)  
**Project Type**: single Python library (`src/air_quality`)  
**Performance Goals**: Handle million+ row tables; vectorized/lazy operations; avoid Python row loops; minimal copies  
**Constraints**: Columnar-first; conversions only at boundaries; deterministic runs (seeded when stochastic)  
**Scale/Scope**: Foundation only; no domain algorithms yet

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The following MUST be explicitly addressed and linked to the design/spec:

- Data schema & mapping: uses centralized three-level column-mapping utility; required canonical fields identified; mapping plan for user inputs; no ad-hoc mapping.
- Architecture: module(s) inherit from `AirQualityModule` and provide `from_dataframe`/`from_dataset`/`run`/`report_dashboard`/`report_cli` with required hooks.
- Performance: large-dataset plan (Polars LazyFrame internally; Arrow/Parquet I/O; vectorized/lazy ops; chunking/streaming if needed; no Python row loops in critical paths).
- Units & provenance: central units registry usage (future); provenance fields attached by `run()`; RNG seed strategy if stochastic.
- Reporting: dashboard `schema_version` and CLI content (inputs, methods, key results, QC/caveats, mapping summary).
- Testing/benchmarks: regression tests for numerics (where applicable); coverage targets; performance baseline/guardrails; validation/doctor CLI coverage (future).
- EJ/health/ethics: safeguards respected by design; no sensitive data exposure in logs.

Gate status: PASS (foundation scope; units registry deferred by design).

## Project Structure

### Documentation (this feature)

```text
specs/001-core-foundation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── air_quality/
│   ├── __init__.py
│   ├── base.py                 # AirQualityModule
│   ├── datasets/
│   │   ├── __init__.py
│   │   └── base.py             # BaseDataset + TimeSeriesDataset (Polars)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── column_mapping.py   # ColumnMapper + ColumnMappingResult
│   │   ├── provenance.py       # ProvenanceRecord + record_provenance
│   │   └── logging.py          # get_logger()
│   └── exceptions.py           # exception taxonomy
└── tests/
    ├── unit/
    │   ├── test_column_mapping.py
    │   ├── test_datasets.py
    │   ├── test_provenance.py
    │   └── test_base_module.py
    └── integration/
        └── test_dummy_module_flow.py
```

**Structure Decision**: Single Python library under `src/air_quality` with `utils/`, `datasets/`, and `exceptions.py`. Tests under `tests/` split into unit and integration.

## Phase 0: Outline & Research

Unknowns: none blocking. Research captured to document key choices and alternatives.

Artifacts to generate:

- `research.md` summarizing columnar backend decision (Polars vs Arrow), mapping strategy, provenance/logging standards.

## Phase 1: Design & Contracts

Artifacts to generate:

- `data-model.md`: Entities (AirQualityModule, BaseDataset, TimeSeriesDataset, ColumnMapper/Result, ProvenanceRecord, Exceptions) with fields and constraints.
- `contracts/air_quality_module.md`: Public interface contracts (method signatures, inputs/outputs, error types, reporting schemas).
- `quickstart.md`: Minimal example to subclass the base and run with a tiny DataFrame.
- Update agent context via `.specify/scripts/bash/update-agent-context.sh copilot` (adds Polars/Arrow decisions).

## Re-check Constitution Gate (post-design)

All gates remain PASS. Units registry implementation explicitly deferred; provenance/reporting/mapping/DRY/performance covered by design.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| None | N/A | N/A |

````markdown
