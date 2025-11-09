# Feature Specification: Feature 003 – Core Statistical Analysis (Descriptive, Correlation, Trends)

**Feature Branch**: `003-stats-core`  
**Created**: 2025-11-09  
**Status**: Draft  
**Input**: User description: "Design and implement Feature 003: Core Statistical Analysis (Descriptive, Correlation, Trends) for the air_quality library."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Descriptive summaries per site/pollutant (Priority: P1)

As an analyst, I want descriptive statistics (mean, median, std, min, max, quantiles, counts) for pollutant concentration columns grouped by canonical keys (e.g., site_id), so I can quickly characterize distributions without sampling or Python loops.

**Why this priority**: Descriptives are foundational and reused in compliance, AQI, EJ, and QC workflows.

**Independent Test**: Provide a small canonical time-series DataFrame (with `datetime`, `site_id`, pollutant columns, and `flag`) and verify the module returns a tidy/long table with one row per group × variable × stat, excluding flagged rows and reporting counts.

**Acceptance Scenarios**:

1. Given a canonical dataset with `site_id` and pollutant columns, When I run DescriptiveStatsModule grouped by `site_id`, Then I receive a tidy table with rows for mean/median/std/min/max/quantiles and counts per pollutant and site.
2. Given some rows have `flag=invalid` or null pollutant values, When I run the module, Then invalid rows are excluded from stats, and counts fields `n_total`, `n_valid`, `n_missing` are consistent.

---

### User Story 2 - Correlations across pollutants with optional grouping (Priority: P2)

As an analyst, I want pairwise correlations (Pearson and Spearman) between pollutant columns overall or per group (e.g., by site), so I can identify relationships among pollutants while knowing sample sizes and avoiding duplicated pairs.

**Why this priority**: Correlations inform multi-pollutant analysis, source apportionment interpretation, and QC anomaly detection.

**Independent Test**: Provide a canonical dataset with two numeric pollutant columns and known correlation; verify returned LazyFrame has one row per pair (including diagonal), includes `n`, and respects grouping.

**Acceptance Scenarios**:

1. Given value columns `[PM25, NO2]`, When I run CorrelationModule with method=`pearson`, Then output contains rows for (PM25, PM25), (PM25, NO2), (NO2, NO2) with `var_x <= var_y` ordering and the expected correlation values and `n`.
2. Given grouping by `site_id`, When I run the module, Then output includes site_id columns with per-group correlations and counts; rows with nulls for either variable are excluded in that pair’s computation.

---

### User Story 3 - Simple linear trends over time (Priority: P3)

As an analyst, I want simple linear trends (value ~ time) for pollutants by group using a chosen time unit (e.g., year), so I can quantify directional change as "unit per time_unit" with `n` reported.

**Why this priority**: Trends are essential for policy, compliance trajectories, and health/EJ narratives.

**Independent Test**: Provide a dataset with a known linear increase per day; verify slope/intercept match expected values for `time_unit="day"`, grouped and ungrouped.

**Acceptance Scenarios**:

1. Given uniformly spaced daily data with slope=+0.5 µg/m³ per day, When TrendModule runs with `time_unit="day"`, Then the returned slope approximates 0.5 with correct `n` and documented unit semantics.
2. Given insufficient valid observations, When TrendModule runs, Then results still report true `n`, and module-level flags indicate `low_n` for downstream reporting.

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

- Non-numeric value columns passed to core primitives → raise `DataValidationError` listing offending columns.
- Mixed units or missing unit metadata for requested pollutant trends → raise `UnitError`.
- Very small sample sizes (`n < min_samples`) → primitives still return values with true `n`; modules flag as `low_n` without raising.
- Duplicated pairs in correlation → enforce single ordered pair `(var_x <= var_y)` including diagonals.
- Flagged/invalid rows present → excluded from computations; counts reflect exclusions.
- No grouping columns provided → global aggregation behaves consistently and returns expected schema.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001 (Core/Descriptive)**: Provide a columnar primitive that computes mean, median, std, min, max, quantiles (5th, 25th, 75th, 95th), count, valid count, and missing count for one or more numeric value columns, with optional grouping.
- **FR-002 (Core/Correlation)**: Provide a primitive that computes pairwise correlations for a list of numeric columns with method in {"pearson", "spearman"}, returning one row per ordered pair `(var_x <= var_y)` with `correlation` and `n`; support optional grouping.
- **FR-003 (Core/Trend)**: Provide a primitive that fits `value ~ time` using closed-form expressions over a chosen `time_unit` in a validated set (e.g., day, month, year), returning `slope`, `intercept`, `n`, and reserved diagnostics fields; support optional grouping.
- **FR-004 (Validation)**: Core primitives MUST validate that all provided value columns are numeric (or safely typed as numeric) and raise `DataValidationError` otherwise; unsupported correlation methods → `ConfigurationError`.
- **FR-005 (QC/Flags)**: All statistical computations MUST exclude rows flagged as invalid/outliers per standardized canonical `flag` semantics from dataset metadata; counts MUST include `n_total`, `n_valid`, `n_missing`.
- **FR-006 (Modules)**: Implement `DescriptiveStatsModule`, `CorrelationModule`, and `TrendModule` inheriting from `AirQualityModule`, delegating heavy computations to core primitives and using `TimeSeriesDataset` + mapping + units/time utilities.
- **FR-007 (Units & Time)**: Trends MUST enforce units presence for target columns; slopes reported as `{Unit} per {time_unit}` using documented definitions; time bounds reported via `time_utils`.
- **FR-008 (Reporting)**: Modules MUST output both dashboard payloads and CLI summaries containing metrics, counts, provenance, and clear notes for low sample sizes and QC filtering.
- **FR-009 (Performance)**: All primitives MUST be expressible with Polars LazyFrame/groupby/expression operations with no Python row loops; include at least one 100k-row smoke/perf test per primitive.
- **FR-010 (Reproducibility)**: Given identical inputs/configs, results MUST be deterministic within documented numeric tolerances.

### Key Entities *(include if feature involves data)*

- **StatisticResult (tidy row)**: `{group_cols...}, variable, stat, value, n_total, n_valid, n_missing`.
- **CorrelationResult (tidy row)**: `{group_cols...}, var_x, var_y, method, correlation, n, p_value (opt), ci_lower (opt), ci_upper (opt)`.
- **TrendResult (tidy row)**: `{group_cols...}, variable, time_unit, slope, intercept, n, r2 (opt), p_value (opt), slope_se (opt), ci_lower (opt), ci_upper (opt), resid_var (opt)`.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001 (Correctness/Descriptive)**: On synthetic datasets with known statistics, mean/median/std/min/max/quantiles match expected values within floating-point tolerance (1e-12 relative for simple cases).
- **SC-002 (Correctness/Correlation)**: Pearson/Spearman outputs on known examples match numpy/scipy references within 1e-12 tolerance for small cases; pair uniqueness and diagonals validated.
- **SC-003 (Correctness/Trend)**: Trend slopes/intercepts for linear synthetic data match analytical values within 1e-12; `time_unit` semantics documented and verified.
- **SC-004 (Performance)**: Each primitive processes ≥100k rows with ≥4 value columns in under 2 seconds on a typical laptop, with no Python-level row loops; memory use does not exceed 2× input size during aggregation.
- **SC-005 (QC Transparency)**: Dashboard/CLI outputs include `n_total`, `n_valid`, `n_missing` and flag derived exclusions; no silent imputation.
- **SC-006 (Reproducibility)**: Repeated runs with same inputs/configurations produce identical outputs; provenance captures pollutants, grouping, methods, thresholds, time bounds.

## Constitution Constraints *(mandatory)*

1. Inheritance & Interface: All new analysis classes (`DescriptiveStatsModule`, `CorrelationModule`, `TrendModule`) inherit `AirQualityModule` and implement required hooks (`_run_impl`, reporting builders, validations). No extra public execution methods beyond the standard interface.
2. Column Mapping: Modules accept pandas inputs via `from_dataframe()` and use the shared `ColumnMapper` to canonicalize columns (e.g., `datetime`, `site_id`, pollutant columns). Strict validation errors on unresolved required fields (`SchemaError`). Mapping metadata preserved in dataset metadata.
3. Units & Provenance: Trends require `Unit` metadata per pollutant; errors via `UnitError` if missing/inconsistent. No implicit conversion; any conversion uses `air_quality.units` and is recorded. Provenance records include module, domain, config hash, selected pollutants, grouping, methods, thresholds, and time bounds.
4. Performance & Scalability: Core primitives operate on Polars LazyFrame with vectorized expressions/groupbys only; no Python row loops. Large datasets (10^5–10^6+ rows) are default; avoid unnecessary materialization; provide 100k-row perf smoke tests.
5. Reporting: Dashboard payloads include module/domain/schema_version/provenance/metrics. CLI reports summarize inputs, QC filtering, key results, and time bounds. Placeholders for uncertainty/diagnostics included in correlation/trend outputs.
6. Testing & Benchmarks: Add regression tests for correctness (including grouped cases), QC filtering, and performance smoke tests. Ensure mypy strictness for new files and maintain existing test pass status.
7. EJ/Health/Ethics: No new sensitive fields introduced. Modules must avoid cherry‑picking and clearly separate statistical summaries from health/compliance claims; privacy safeguards N/A for this core feature.
8. DRY & Shared Utilities: All heavy logic in `air_quality.stats_analysis.core`; modules are thin orchestrators. Reuse shared logging, mapping, units, provenance, and time utilities; no duplicated statistical code.
9. Security & Privacy: No credentials handled. Logs emit only non‑sensitive metadata (selected columns, counts). Respect any sensitive dataset metadata by not logging raw identifiers.
10. Versioning Impact: Adds new public APIs (modules + core layer) → MINOR version bump. No changes to existing scientific results. Migration notes to include how to adopt new modules.
