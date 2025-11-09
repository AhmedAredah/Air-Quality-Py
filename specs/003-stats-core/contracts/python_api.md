# API Contracts – Feature 003 (Python)

## Core Primitives (stats_analysis.core)

### descriptive.compute_descriptives(
- dataset: TimeSeriesDataset,
- group_by: list[str] | None,
- pollutant_col: str = "pollutant",
- conc_col: str = "conc",
- flag_col: str = "flag",
) -> polars.DataFrame | pandas.DataFrame
- Errors: DataValidationError (non-numeric), SchemaError (missing columns)
- Notes: Excludes invalid/outlier; treats below_dl as missing

### correlation.compute_pairwise(
- dataset: TimeSeriesDataset,
- group_by: list[str] | None,
- method: Literal["pearson", "spearman"] = "pearson",
- pollutant_col: str = "pollutant",
- conc_col: str = "conc",
- flag_col: str = "flag",
) -> polars.DataFrame | pandas.DataFrame
- Errors: ConfigurationError (unsupported method)
- Notes: Ordered pairs var_x <= var_y, include diagonal, report n

### trend.compute_linear(
- dataset: TimeSeriesDataset,
- group_by: list[str] | None,
- time_unit: Literal["hour", "day", "calendar_month", "calendar_year"],
- min_duration_years: float = 1.0,
- pollutant_col: str = "pollutant",
- conc_col: str = "conc",
- flag_col: str = "flag",
) -> polars.DataFrame | pandas.DataFrame
- Errors: UnitError (missing units), DataValidationError (non-numeric)
- Notes: Calendar-aware elapsed time; returns slope, intercept, n, short_duration_flag

## Modules (air_quality.modules)

### DescriptiveStatsModule(AirQualityModule)
- Config: group_by, quantiles=(0.05,0.25,0.75,0.95)
- Output: StatisticResult rows, dashboard payload, CLI summary

### CorrelationModule(AirQualityModule)
- Config: group_by, method={pearson,spearman}, allow_missing_units=False
- Output: CorrelationResult rows with n; provenance includes units_status

### TrendModule(AirQualityModule)
- Config: group_by, time_unit, min_samples=3, min_duration_years=1.0
- Output: TrendResult rows, with flags and provenance (bounds, duration, thresholds)
