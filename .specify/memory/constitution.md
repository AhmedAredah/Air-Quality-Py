<!--
Sync Impact Report
Version: (initial) → 1.0.0
Modified Principles: Replaced placeholder core principles with fully defined 16-section framework.
Added Sections: Mission & Scope; Regulatory & Scientific Standards; Data & Metadata Standards; Modeling & Statistical Standards; Quality Control & Validation; Environmental Justice, Health, and Ethics; Core Architecture & AirQualityModule Interface; Reporting & Visualization; API Design, Error Taxonomy & Documentation; Testing, Benchmarking & Reproducibility; Performance, Scalability & Remote Data; Versioning, Backwards Compatibility & Deprecation; Security, Privacy & Compliance Data; Contribution, Core vs Experimental Modules & Governance; Provenance, Units & Reproducibility Extensions; Accessibility, Interoperability & Ethical Modeling; Governance.
Removed Sections: None (template placeholders superseded).
Templates Updated: ✅ .specify/templates/plan-template.md (Constitution Check gating) | ✅ .specify/templates/spec-template.md (Constitution Constraints guidance) | ✅ .specify/templates/tasks-template.md (Foundational tasks & invariants) | ⚠ README.md (currently empty; recommend population with quickstart + constitution reference) | ⚠ No commands/ directory present (cannot update command files referenced in prompt).
Deferred TODOs: None.
Amendment Type: Initial adoption sets baseline version 1.0.0.
-->

# air_quality Constitution

**Purpose**: Establish non‑negotiable, testable governance, scientific, architectural, performance, and ethical standards for the `air_quality` Python library. All future `/speckit.*` artifacts MUST comply.

---

## 1. Mission & Scope

* Provide high‑quality, transparent, reproducible air‑quality analysis and source apportionment for research, regulatory, policy, and environmental justice workflows.
* Support both exploratory analysis and production‑grade pipelines with deterministic, provenance‑rich outputs.
* Treat large datasets (multi‑year, multi‑site, high‑resolution) as the default case; prioritize algorithmic efficiency, memory discipline, columnar storage (PyArrow or equivalent), and vectorized computation.
* Architectural and scientific rules herein are global invariants; module‑specific tuning occurs in module configs without weakening core standards.
* Enforce rigorous separation between data ingestion, canonicalization, computation, reporting, and provenance recording.

---

## 2. Regulatory & Scientific Standards

* Align units, pollutants, averaging times, AQI definitions with major authorities (US EPA, EEA, WHO); discrepancies MUST be explicitly documented.
* Core algorithms (PMF, CMB, UNMIX; health/EJ metrics; compliance calculations; biomonitoring indices) MUST implement peer‑reviewed or regulatory standard formulas with cited references in docstrings and docs.
* Biomonitoring metrics MUST document: species list, index definitions, calibration region/climate, interpretation (ambient proxy vs ecosystem impact), and caveats when extrapolated to health/EJ narratives.
* Compliance modules MUST implement design values, exceedance counts, calendar vs regulatory year aggregations; every report MUST state which convention was used.
* Undocumented “black box” methods are PROHIBITED.
* Deviations from standard practice MUST be labeled `experimental` or `non_standard` in API, metadata, dashboard, and CLI outputs with justification.

---

## 3. Data & Metadata Standards

* Mandatory canonical columns by dataset type:
	* Time series: `datetime`, `site_id`, `pollutant`/`species_id`, `conc`, `unc` (if available), `flag`.
	* Speciation: `datetime`, `site_id`, `species_id`, `conc`, `unc`, `dl` (detection limit), `flag`, `method_id`.
	* Spatial: `geometry` or (`lat`,`lon`), `site_id`, CRS metadata, resolution, `pollutant`, `conc`.
	* Biomonitoring: `datetime` (or period), `site_id`, `bioindicator_id`, `metric_type`, `value`, `unit`, `flag`.
* Time standards: store timestamps in UTC (naive internal) plus explicit `timezone` metadata; daylight savings handling documented; regulatory local‑time conventions recorded.
* Sampling/averaging interval MUST be recorded (`interval_minutes` or similar) and validated against standard definitions.
* Missingness & censoring:
	* Distinguish categories: `missing`, `below_dl`, `invalid` (flagged); store structured flags not free‑text.
	* Imputation MUST be explicit, logged, and reported (dashboard + CLI) with method, parameters, seed.
	* Silent imputation is PROHIBITED.
* Three‑level column mapping utility (single shared module):
	1. Explicit mapping dict `{canonical -> user_column}` (authoritative; incomplete mapping → error).
	2. Safe fuzzy mapping (synonym heuristics, never silent; ambiguity or absence → error with guidance).
	3. Strict validation: any unresolved required field → structured `SchemaError` listing missing/ambiguous fields and attempted synonyms.
* Canonicalization requirements:
	* Preserve original column names; store mapping metadata `{canonical: original}`.
	* Dashboard + CLI MUST show a “Data schema / mapping” section for each run.
	* All analysis modules MUST consume canonical dataset objects, never raw user DataFrames.
* FAIR behavior: stable `dataset_id`, searchable metadata (`site_id`, `pollutant`, `time_range`); support storage/reload via Parquet/Arrow, NetCDF; maintain provenance, licensing, references.
* Large datasets: internal representation MUST be columnar (PyArrow Table/Dataset or equivalent). Pandas/xarray views only at boundaries. Support chunked / out‑of‑core processing for memory‑bound workloads.

---

## 4. Modeling & Statistical Standards

* PMF/CMB/UNMIX modules MUST implement: explicit uncertainty matrices, DL treatment, censoring strategy, reproducible seeds, diagnostics (Q/Qexp, residuals, interpretability), convergence and sensitivity analyses (multiple starts, rotations/FPEAK documented).
* Statistical analyses MUST check and log assumptions (normality, homoscedasticity, independence) where applicable; effect sizes and confidence intervals accompany p‑values.
* P‑hacking patterns (undisclosed repeated model re‑specification) are PROHIBITED.
* Imputation/forecast/trend modules: parameterized, no in‑place silent modification; output new dataset objects with provenance.
* Heavy operations on large data MUST be vectorized (NumPy/xarray/PyArrow/Polars) – Python loops in critical paths are PROHIBITED.

---

## 5. Quality Control & Validation

* QA/QC MUST include: calibration checks, instrument performance indicators, outlier detection rules, completeness metrics, validation against reference sites/datasets where available.
* Each module MUST implement at least one validation strategy: cross‑validation, hold‑out, reference comparison, or synthetic/Monte Carlo experiments.
* Malformed/suspicious inputs → explicit errors or warnings; warnings surfaced in dashboard + CLI.
* QC/validation outputs stored in `results` under standardized keys and exposed in reports.

---

## 6. Environmental Justice, Health, and Ethics

* EJ and vulnerable populations are first‑class: disparity metrics, cumulative burden, distribution‑aware summaries (quantiles by group/community).
* Visualization/reporting MUST avoid cherry‑picking; separate legal compliance from health guideline exceedance.
* All thresholds/value judgments (percentiles, hotspot labels, EJ definitions) MUST be documented with references.
* Privacy‑aware handling: sensitive subgroup data aggregated or masked per Security & Privacy rules.

---

## 7. Core Architecture & AirQualityModule Interface (DRY)

* Single root base class: `AirQualityModule` (`air_quality/base.py`). All core and experimental modules MUST inherit directly or indirectly.
* Public entrypoints: `from_dataframe()`, `from_dataset()`, `run()`, `report_dashboard()`, `report_cli()` – no additional public execution methods.
* Standard invariants: `MODULE_NAME`, `DOMAIN`, `OUTPUT_SCHEMA_VERSION`.
* Required attributes: `dataset`, `config`, `results`, `metadata`, `provenance`, `logger`.
* Required hooks: `_run_impl()`, `_build_dashboard_report_impl()`, `_build_cli_report_impl()`, `_validate_config_impl()`, `_get_required_columns()`, `_dataset_from_mapped_df()`, `_validate_dataset()` (extendable + super call).
* Column mapping MUST use shared utility; no module‑specific ad‑hoc mapping logic.
* Core dataset types (`SpeciationDataset`, `TimeSeriesDataset`, `SpatialDataset`, etc.) constructed only via canonical mapping.
* DRY enforcement: shared logic (aggregation, units, QC, provenance, logging) lives in centralized utilities/mixins – duplication triggers refactor before merge.

---

## 8. Reporting & Visualization (Dashboard + CLI)

* Each module produces two reports: structured dashboard payload + human‑readable CLI text.
* Dashboard payload MUST include: module name, metrics (value + units), time/site scopes, uncertainties, flags, provenance, `schema_version`.
* CLI report MUST include: inputs summary, methods, key results, QC warnings, limitations, data mapping summary.
* Central dashboard layer discovers modules, aggregates multi‑module outputs, and renders composite or module‑specific views.
* Alternative/bypassing report channels for core modules are PROHIBITED.

---

## 9. API Design, Error Taxonomy & Documentation

* Consistent parameter naming (e.g., `site_id`, `pollutant`, `start_time`, `end_time`).
* Standard exception taxonomy: `SchemaError`, `DataValidationError`, `UnitError`, `AlgorithmConvergenceError`, `ConfigurationError`, `PerformanceWarning`.
* Public APIs MUST document raised exceptions; failures degrade gracefully (partial results + explicit error section) instead of crashing pipelines.
* Comprehensive docstrings: parameters (units, shapes), returns (units), exceptions, references, minimal example.
* Narrative docs for: PMF/CMB/UNMIX, temporal/spatial analyses, health/EJ metrics, compliance, biomonitoring, reporting, column mapping workflows.

---

## 10. Testing, Benchmarking & Reproducibility

* Minimum coverage thresholds for core logic (target value defined in CI config).
* Regression tests for numerical algorithms with stable reference outputs; tolerance windows documented where bitwise determinism infeasible.
* Deterministic stochastic methods via explicit seeds; unseeded global RNG usage PROHIBITED.
* Tests for both reporting modes per module.
* Column mapping utility tests: explicit, fuzzy, error paths.
* Performance regression tests/benchmarks on representative large datasets; CI fails on significant degradation.
* CLI `air_quality validate`: schema/unit/mapping/QC checks.
* CLI `air_quality doctor`: environment diagnostics (versions, BLAS, columnar backends).
* Reproducibility: pinned dependencies, example notebooks, CLI ↔ SDK parity.

---

## 11. Performance, Scalability & Remote Data

* Target scales: millions of rows, hundreds of sites, high‑resolution spatial grids – documented in performance guide.
* Memory discipline: avoid unnecessary copies; prefer views/in‑place where safe; chunk/stream large inputs.
* Expensive ops expose progress, chunking, optional parallelization.
* Columnar data structures (PyArrow/Polars) REQUIRED for large tabular operations; CSV reserved for small examples.
* Row‑wise Python loops in performance‑critical paths PROHIBITED; require vectorization or backend acceleration.
* Optional distributed integration (Dask/Ray/Spark) allowed at orchestration layer; algorithms remain backend‑friendly.
* Remote data (S3/GCS/Azure URIs): use lazy scan readers, config‑driven credentials, never log secrets.

---

## 12. Versioning, Backwards Compatibility & Deprecation

* Semantic versioning (MAJOR.MINOR.PATCH) governs library releases.
* Versioned schemas: dashboard output, dataset schemas, mapping utility behavior.
* Any change affecting scientific results or schema → at least MINOR bump; breaking changes → MAJOR.
* Deprecations announced via release notes + runtime warnings ≥ one MINOR release before removal.
* Migration notes required for changes to scientific methods, schemas, units, mapping logic.
* Legacy slow code paths: marked, emit `PerformanceWarning`, scheduled removal timeline documented.

---

## 13. Security, Privacy & Compliance Data

* Sensitive EJ/health data fields labeled; raw identifiers (person IDs, exact addresses) never logged.
* Logs contain only aggregated/non‑sensitive metadata.
* Minimum population thresholds enforced; small counts suppressed or aggregated.
* Remote/cloud credentials: configuration only; never hard‑coded or logged.

---

## 14. Contribution, Core vs Experimental Modules & Governance

* Contributions MUST meet: style, linting, tests, documentation, scientific citations, performance considerations.
* Core modules: full compliance with all sections; strict backwards compatibility.
* Experimental modules: inherit `AirQualityModule`, implement reporting, label clearly; relaxed internal stability allowed but MUST meet safety, transparency, EJ, and mapping standards.
* New features/algorithms: include citations, validation (synthetic or real data), comparative benchmarks.
* Reviewers reject PRs with: scientific rigor gaps, EJ/health bypass, ad‑hoc mapping, inefficient data handling, duplicated logic.

---

## 15. Provenance, Units & Reproducibility Extensions

* Provenance record MUST include: data source IDs, ingestion timestamp, transformations, mapping strategy, algorithm version, configuration hash, random seed, checksum.
* `run()` (or shared helper) attaches provenance uniformly; reports expose core fields.
* Uncertainty handling: outputs include uncertainty metrics or explicit `uncertainty: not_applicable` flag.
* Composite indices MUST document uncertainty propagation method.
* Resampling/simulation modules MUST report iterations and diagnostics.
* Central units registry ensures canonical internal units; ingestion converts or errors on unknown units; user‑facing conversions only at reporting layer.
* Rounding/precision policy defined per pollutant (document in units registry) for consistent reporting.
* Structured logging (JSON/key‑value) mandatory; significant events (mapping, imputation, QC, convergence issues) logged at appropriate level.
* Configuration: explicit serializable objects; recorded in provenance; no undocumented globals.

---

## 16. Accessibility, Interoperability & Ethical Modeling

* Visualization defaults: color‑blind safe, adequate contrast, perceptually uniform scales for choropleths.
* Spatial plots include legends, units, data sources, masking/aggregation notes.
* Provide textual summaries/alt‑text for key dashboard figures where feasible.
* Benchmark datasets (or references) per major domain; end‑to‑end example pipelines (PMF workflow, multi‑year AQI/compliance, EJ disparity) under test for regression stability.
* Interoperability: pandas/xarray, GeoPandas, NetCDF, Parquet/Arrow (PyArrow primary backend); consider CF conventions / EPA AQS tags where practical.
* Dashboard outputs adhere to documented JSON schema enabling external integration.
* Reproducibility manifest: JSON/YAML capturing versions, OS, configs, seeds.
* ML modules: document model type, training data provenance, evaluation metrics; fairness/distributional checks for EJ/health impacts; proprietary opaque models flagged and documented.

---

## Governance

* This constitution supersedes conflicting project practices; all design, implementation, and review phases MUST perform a “Constitution Check”.
* Amendments require: proposed diff, rationale (scientific/performance/ethical), version impact assessment (PATCH/MINOR/MAJOR), migration considerations, and maintainer approval.
* Version Increments:
	* PATCH: wording clarifications, non‑semantic doc updates, internal refactors with no API/result change.
	* MINOR: additive principles/sections, new validated algorithms, schema extensions backward compatible.
	* MAJOR: removals, breaking behavioral changes, schema incompatibilities, altered scientific formulas impacting results.
* Compliance Review: each PR MUST include checklist covering sections 3, 7, 8, 9, 10, 11, 15 (data schema, architecture, reporting, API/doc, tests, performance, provenance/units). CI may enforce automated gates.
* Enforcement: Non‑conforming contributions are blocked until rectified; emergency fixes may temporarily bypass performance benchmarks but MUST schedule remediation.
* Sunset Policy: experimental features either promoted (with validation + docs) or deprecated after defined evaluation window.

---

## AI Assistant Enforcement Directive

The AI assistant MUST treat all principles herein as non‑negotiable guardrails for future `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, and `/speckit.implement` runs. It MUST always enforce:

1. `AirQualityModule` inheritance and interface (`from_dataframe` / `from_dataset` / `run` / `report_dashboard` / `report_cli` + required hooks).
2. Dual reporting modes (dashboard structured + CLI text).
3. Centralized three‑level column mapping utility (explicit → safe fuzzy → strict error) with metadata logging.
4. Central units registry, provenance, and uncertainty policies.
5. Efficient, columnar large‑dataset handling (PyArrow or equivalent) and performance‑aware, vectorized algorithms.
6. Strict DRY for shared logic; no duplicated implementations of mapping, aggregation, units, QC, logging, provenance.
7. Canonical dataset objects (e.g., `SpeciationDataset`, `TimeSeriesDataset`, `SpatialDataset`) required for all data‑facing modules.
8. Comprehensive testing, benchmarking, and reproducibility (seeds, manifests, validation CLI tools).
9. EJ, health, ethics, privacy safeguards in analysis and reporting.
10. Explicit documentation and labeling for experimental/non‑standard methods.

All generated specs/plans/tasks MUST cross‑reference this constitution when invoking related constraints (units, EJ metrics, performance benchmarks, column mapping, inheritance, reporting interface, provenance, DRY).

**Version**: 1.0.0 | **Ratified**: 2025-11-08 | **Last Amended**: 2025-11-08
