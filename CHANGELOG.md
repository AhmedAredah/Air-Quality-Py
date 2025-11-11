# Changelog

All notable changes to the `air-quality` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Core Statistical Analysis (Feature 003: 003-stats-core) - MINOR bump

#### Statistical Primitives (`analysis/` package)

- **Descriptive Statistics** (`descriptive.py`):
  - `compute_descriptives()` function for mean, median, std, min, max, quantiles
  - Support for multiple value columns (analyze temperature, humidity, pressure in single call)
  - Tidy (long) and wide (pivot) output formats via `OutputFormat` enum
  - Generic design: works with any time series data, not just air quality
  - QC-aware: excludes invalid/outlier, treats below_dl as missing
  - Performance: Lazy evaluation, single-pass aggregation, zero early materializations

- **Correlation Analysis** (`correlation.py`):
  - `compute_pairwise()` for Pearson and Spearman correlations
  - Ordered unique pairs (var_x <= var_y lexicographically)
  - Diagonal pairs included (self-correlation = 1.0)
  - Global or grouped correlation modes
  - Unit enforcement with allow_missing_units override
  - Scipy integration for Spearman rank transforms

- **Trend Analysis** (`trend.py`):
  - `compute_linear_trend()` for OLS regression (conc ~ time)
  - Calendar-aware time units: HOUR, DAY, CALENDAR_MONTH, CALENDAR_YEAR
  - Closed-form OLS using sufficient statistics (no iterative solvers)
  - Duration and sample-size quality flags (short_duration_flag, low_n_flag)
  - Slope units computed automatically (e.g., "ug/m3/day", "ppb/calendar_year")
  - Fractional year computation for calendar units (handles leap years)

#### Statistical Modules (`modules/statistics/` package)

- **DescriptiveStatsModule** (`descriptive.py`):
  - Orchestrates `compute_descriptives` with grouping and QC filtering
  - Enum-based configuration: `DescriptiveStatsConfig`
  - Dashboard payload with statistics list, QC summary, time bounds
  - CLI report with tidy table format
  - Provenance integration (automatic via base module)

- **CorrelationModule** (`correlation.py`):
  - Orchestrates `compute_pairwise` with method selection and grouping
  - Enum-based configuration: `CorrelationConfig`
  - Dashboard payload with correlations, method, n_pairs, units_status
  - CLI report with correlation matrix and top correlations
  - Unit override warning in CLI when allow_missing_units=True

- **TrendModule** (`trend.py`):
  - Orchestrates `compute_linear_trend` with time unit and thresholds
  - Enum-based configuration: `TrendConfig`
  - Dashboard payload with trends, time_unit, n_trends, time_bounds
  - CLI report with slopes, intercepts, R², quality flags
  - Flag display for short duration and low sample counts

#### Architecture Patterns

- **Config Enums**: All modules use inline `(str, Enum)` config classes for type safety
- **Operation/Result Enums**: Standardized enum-based result storage
- **Provenance Integration**: Automatic provenance via `make_provenance()` from `provenance.py`
- **Lazy Evaluation**: All primitives return Polars LazyFrame (no early collect())
- **Zero-Copy Construction**: `from_polars()` method on BaseDataset and TimeSeriesDataset

#### Performance Optimizations

- Single-pass aggregation in descriptive statistics (eliminated redundant group_by)
- Lazy evaluation throughout (query optimizer can fuse operations)
- QC filtering with materialization points to avoid Polars optimizer issues
- Closed-form OLS for trends (no iterative solvers like scipy.optimize)
- Performance targets met: 100k rows in <2 seconds for all primitives

#### Testing (137+ tests, 100% passing)

- **Unit Tests** (75 tests):
  - Descriptive: basic, grouped, flags, wide format (38 tests)
  - Correlation: Pearson, Spearman, grouped, units (33 tests)
  - Trend: basic, calendar units, short duration, units (28 tests)

- **Integration Tests** (21 tests):
  - Module CLI reports and dashboard payloads
  - Provenance integration
  - QC filtering and edge cases

- **Performance Tests** (16 tests):
  - 100k row benchmarks for all primitives
  - Multi-pollutant and grouped scenarios
  - Calendar year time unit performance

#### Type Safety

- mypy --strict passes for all analysis/ and modules/statistics/ code
- Type annotations for all public functions
- Type guards for optional parameters
- Proper handling of pandas ExtensionArray and Polars schema types

#### Documentation

- **Quickstart Guide** (`specs/003-stats-core/quickstart.md`):
  - Comprehensive examples for all 3 modules
  - Basic usage, grouped analysis, custom configuration
  - Results structure documentation

- **README Section**: Feature 003 overview with code examples
- **Research Notes** (`specs/003-stats-core/research.md`):
  - Calendar-aware time conversion rationale
  - Closed-form OLS derivation
  - Performance optimization strategies

#### Dependencies

- scipy (Spearman rank transforms)
- No new external dependencies beyond Phase 1-2

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
