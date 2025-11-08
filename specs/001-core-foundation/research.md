# Research: Foundational Core Decisions

Date: 2025-11-08  
Branch: 001-core-foundation

## Decision: Internal Columnar Backend = Polars LazyFrame

- Rationale: Lazy query optimization, strong columnar performance, ergonomic API; aligns with constitution’s vectorized/columnar-first requirement.
- Alternatives considered:
  - PyArrow Table as sole internal: Excellent interchange/I-O, but lacks lazy expression engine; better as boundary/interchange.
  - pandas DataFrame: Row-oriented, slower for very large datasets; acceptable only at boundaries.

## Decision: Interchange & Storage = PyArrow Table / Parquet

- Rationale: Ubiquitous columnar format with rich ecosystem; efficient for large-scale I/O; zero-copy conversions where possible.
- Alternatives considered: CSV (discouraged beyond small examples), Feather (viable but Parquet more common and feature-rich).

## Decision: Three-Level Column Mapping Utility

- Rationale: Enforces explicit → safe fuzzy → strict error, preventing silent misinterpretation; DRY across modules.
- Notes: Synonyms are per-field; ambiguity and missing fields produce structured SchemaError with candidates tried.

## Decision: Provenance & Logging

- Rationale: Standardize provenance fields (module, domain, dataset_id, config_hash, timestamp, version); structured logging via a shared helper for consistency.
- Alternatives considered: Ad-hoc per-module logging/provenance (rejected by DRY and reproducibility requirements).

## Decision: Testing & Determinism

- Rationale: Unit + integration tests for mapper, datasets, base lifecycle; deterministic seeds when stochastic; tolerance for numerical variants handled later per algorithm.

