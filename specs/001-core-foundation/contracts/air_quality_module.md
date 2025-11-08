# Contract: AirQualityModule Interface

## Class Invariants

- MODULE_NAME: str
- DOMAIN: str
- OUTPUT_SCHEMA_VERSION: str

## Constructors

### from_dataframe(df, *, config=None, column_mapping=None, metadata=None, column_mapper=None)

- Inputs: df (pandas.DataFrame), config (dict), column_mapping (dict canonical->original), metadata (dict), column_mapper (ColumnMapper or None)
- Behavior: Performs mapping (explicit → fuzzy → validation) using required columns from subclass; constructs dataset via _dataset_from_mapped_df.
- Errors: SchemaError (missing/ambiguous columns), ConfigurationError (invalid config fields)

### from_dataset(dataset, *, config=None, metadata=None)

- Inputs: dataset (BaseDataset), config (dict), metadata (dict)
- Behavior: Wraps existing canonical dataset; performs config validation.
- Errors: ConfigurationError

## Lifecycle

### run()

- Pre: dataset validated (_validate_dataset), config validated (_validate_config_impl)
- Actions: executes _run_impl, records timing, attaches provenance using record_provenance
- Post: results (dict) populated; provenance set
- Returns: self
- Errors: SchemaError/DataValidationError (invalid dataset), AlgorithmConvergenceError (future algorithms), ConfigurationError

## Reporting

### report_dashboard()

- Returns: dict containing keys: module, domain, schema_version, provenance (dict), metrics (module-specific from `_build_dashboard_report_impl`)

### report_cli()

- Returns: str human-readable summary (includes inputs, methods, key results, QC/warnings, mapping summary)

## Required Subclass Hooks

- _get_required_columns() -> dict[str, list[str]] | list[str]
- _dataset_from_mapped_df(mapping_result: ColumnMappingResult) -> BaseDataset
- _run_impl() -> None
- _build_dashboard_report_impl() -> dict[str, Any]
- _build_cli_report_impl() -> str
- _validate_config_impl() -> None
- _validate_dataset() -> None (base provides, subclass may extend)

## Dataset Abstraction

### BaseDataset

- data: Polars LazyFrame
- metadata: dict
- mapping: dict canonical->original
- Methods: n_rows, is_empty(), get_column(name), get_dataset_id()

### TimeSeriesDataset (BaseDataset)

- Required Columns: datetime, site_id, pollutant/species_id, conc
- Optional Columns: unc, flag
- Constructors: from_arrow(table, metadata), from_pandas(df, metadata)
- Conversions: to_arrow(), to_pandas()

## Column Mapping

### ColumnMapper.map(df, *, required_columns, user_mapping, domain, module_name)

- Phases: explicit → fuzzy (synonyms) → strict validation
- Returns: ColumnMappingResult (df_mapped, mapping, unmapped_columns, metadata diagnostics)
- Errors: SchemaError (missing/ambiguous)

## Provenance

### record_provenance(module_name, domain, dataset, config, metadata)

- Produces ProvenanceRecord with dataset_id, config_hash (JSON normalized), timestamp, version
- ProvenanceRecord.to_dict() returns JSON-serializable dict

## Exceptions

- SchemaError, DataValidationError, UnitError, AlgorithmConvergenceError, ConfigurationError
- PerformanceWarning (Warning subclass) for non-optimal paths (e.g., fallback to pandas)

## Performance Considerations

- No row-wise Python loops in mapping or run lifecycle
- LazyFrame operations used for column selection/renaming
- Conversions to Arrow/pandas performed only when explicitly requested by user

