# Changelog

All notable changes to the `air-quality` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.1.0] - 2025-01-XX

### Core Foundation (Specification: 001-core-foundation)

- **Exception Taxonomy** (`exceptions.py`):
  - `AirQualityError` base class
  - 6 specialized exceptions: `ConfigurationError`, `DataValidationError`, `ColumnMappingError`, `ProvenanceError`, `AnalysisRuntimeError`, `ReportingError`
  - Hierarchical error handling with detailed context

- **Structured Logging** (`logging.py`):
  - `StructuredLogger` class with module/domain/level context
  - JSON-serializable log records
  - Configurable log levels and propagation

- **Provenance Tracking** (`provenance.py`):
  - `ProvenanceManager` for deterministic SHA-256 hashing
  - Captures: input data, configuration, code version, dependencies
  - Reproducibility guarantees via locked versioning

- **Column Mapping** (`mapping.py`):
  - `ColumnMapper` with 3-level resolution: explicit → synonyms → fuzzy
  - `MappingResult` with canonical columns and detailed diagnostics
  - Fuzzy matching via `fuzzywuzzy` with configurable thresholds
  - Performance: >100M rows/sec on 1M row datasets

- **Dataset Abstractions** (`dataset/`):
  - `BaseDataset` abstract class with Polars LazyFrame backend
  - `TimeSeriesDataset` with time index enforcement
  - Zero-copy conversions to Arrow/pandas
  - Lazy computation with deferred execution

- **Base Module** (`module.py`):
  - `AirQualityModule` single-root base class
  - Standardized lifecycle: validate → run → report → provenance
  - `DashboardPayload` TypedDict for IDE type hints
  - `from_dataframe()` factory with automatic mapping + dataset construction
  - Dashboard (JSON) and CLI (text) reporting

- **Testing**:
  - 73 comprehensive tests (100% passing)
  - Test categories: exceptions, logging, provenance, mapping, dataset, module lifecycle, performance
  - Performance benchmarks: copy behavior, mapping scalability, memory efficiency

- **Type Safety**:
  - mypy configured with pandas-stubs and pyarrow-stubs
  - All type checks passing (11 source files)
  - `py.typed` marker for downstream type checking

- **Documentation**:
  - README.md with installation, architecture, examples
  - Quickstart guide with RowCountModule demo
  - Provenance rationale and performance metrics
  - CHANGELOG.md (this file)

### Performance

- Column mapping: >100M rows/sec (explicit & fuzzy) on 1M rows
- Linear scaling verified (10K → 1M rows)
- Zero unnecessary DataFrame copies
- LazyFrame deferred computation validated

### Dependencies

- Python >= 3.12 (required)
- Polars >= 0.20.3 (columnar backend)
- pandas, pyarrow (boundary conversions)
- fuzzywuzzy, python-Levenshtein (fuzzy matching)
- pytest (testing)

---

## Project Links

- **Repository**: [GitHub](https://github.com/your-org/air-quality) *(update with actual URL)*
- **Issues**: [GitHub Issues](https://github.com/your-org/air-quality/issues) *(update with actual URL)*
- **Documentation**: See `README.md` and `specs/001-core-foundation/`
