# Data Model: Foundational Core

Date: 2025-11-08  
Branch: 001-core-foundation

## Entities

### AirQualityModule

- Purpose: Template-method base for all analysis modules.
- Key Fields: dataset (BaseDataset), config (dict), metadata (dict), results (dict), provenance (ProvenanceRecord), logger.
- Invariants: MODULE_NAME, DOMAIN, OUTPUT_SCHEMA_VERSION.
- Hooks: `_run_impl()`, `_build_dashboard_report_impl()`, `_build_cli_report_impl()`, `_validate_config_impl()`, `_get_required_columns()`, `_dataset_from_mapped_df()`, `_validate_dataset()`.
- Behavior: run() orchestrates validation, execution, timing, provenance.

### BaseDataset

- Purpose: Abstract canonical dataset wrapper.
- Fields: data (Polars LazyFrame), metadata (dict), mapping (dict canonical->original optional).
- Methods: n_rows (property), is_empty(), get_column(name), get_dataset_id().
- Constraints: Internal storage MUST remain columnar (LazyFrame); conversions explicit.

### TimeSeriesDataset (inherits BaseDataset)

- Additional Expected Columns: datetime, site_id, pollutant/species_id, conc, optional unc, flag.
- Constructors: from_arrow(table, metadata), from_pandas(df, metadata) converting to LazyFrame internally.
- Conversion: to_arrow(), to_pandas() boundary helpers.

### ColumnMapper

- Purpose: Central three-level mapping (explicit → fuzzy → validation).
- Inputs: df, required_columns (dict canonical -> synonyms list), user_mapping (dict), domain, module_name.
- Outputs: ColumnMappingResult
- Errors: SchemaError for missing/ambiguous fields.

### ColumnMappingResult

- Fields: df_mapped (DataFrame/LazyFrame view), mapping (dict canonical->original), unmapped_columns (list), metadata (dict diagnostics).

### ProvenanceRecord

- Fields: module_name, domain, dataset_id, config_hash, run_timestamp, software_version, extra (dict).
- Methods: to_dict().

### Exceptions

- SchemaError/DataValidationError, UnitError, AlgorithmConvergenceError, ConfigurationError, PerformanceWarning.
- Purpose: Standard taxonomy for failure modes; PerformanceWarning indicates non-optimal path.

## Relationships

- AirQualityModule consumes BaseDataset/TimeSeriesDataset.
- ColumnMapper produces mapping consumed by dataset constructors.
- ProvenanceRecord attached after run() completes.

## Validation Rules

- Required canonical columns present post-mapping before dataset construction.
- dataset.is_empty() must raise validation error in run().
- mapping ambiguity results in SchemaError listing candidates.

## State Transitions

- Module lifecycle: constructed → run() invoked (results + provenance populated) → reporting.
- Dataset remains immutable except explicit conversions (no hidden mutation of canonical fields).

