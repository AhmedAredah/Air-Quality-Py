# Implementation Plan: Feature 003 – Core Statistical Analysis (Descriptive, Correlation, Trends)

**Branch**: `003-stats-core` | **Date**: 2025-11-09 | **Spec**: specs/003-stats-core/spec.md
**Input**: Feature specification from `/specs/003-stats-core/spec.md`

## Summary

Implement three analysis modules backed by vectorized core primitives over canonical long time-series data:
- Descriptive summaries per pollutant and group
- Pairwise correlations (Pearson, Spearman) with ordered unique pairs and counts
- Simple linear trends with calendar-aware time unit semantics

All computations exclude `invalid`/`outlier` rows; treat `below_dl` as missing; enforce units for trends; correlation requires units by default but allows override; minimum samples default to 3 and minimum trend duration default to 1 year are configurable and flagged in provenance.

## Technical Context

**Language/Version**: Python 3.12 (per `pyproject.toml`)  
**Primary Dependencies**: Polars (vectorized groupby/aggregations), Pandas (boundary helpers), PyArrow (columnar storage), NumPy/SciPy (reference checks in tests), pytest, mypy  
**Storage**: Parquet/Arrow files when persisted; in-memory Polars/Pandas during analysis  
**Testing**: pytest (unit + regression + perf smoke tests); mypy strict for new files  
**Target Platform**: Cross-platform (Windows/macOS/Linux); local CPU execution  
**Project Type**: Single Python library (src layout)  
**Performance Goals**: Each primitive handles ≥100k rows with ≥4 value columns in < 2s; no Python row loops; memory ≤ 2× input during aggregation (Spec SC-004; Constitution Sec. 11)  
**Constraints**: Columnar-first, vectorized operations; deterministic outputs; dual reporting (dashboard JSON + CLI text); reuse mapping/units/provenance utilities; no silent imputation  
**Scale/Scope**: Multi-site, multi-year time series (10^5–10^6+ rows typical)

NEEDS CLARIFICATION: None blocking. Diagnostics fields (p_value, CIs) are placeholders in this phase; documented as reserved for future extension.

## Constitution Check

Gate status: PASS (no unresolved blockers)

- Data schema & mapping: Will accept inputs via `from_dataframe()` and construct `TimeSeriesDataset` using shared `ColumnMapper` (Sec. 3 & 7). Canonical fields: `datetime`, `site_id`, `pollutant`/`species_id`, `conc`, optional `unc`, `flag`. No ad-hoc mapping.
- Architecture: New `DescriptiveStatsModule`, `CorrelationModule`, `TrendModule` inherit `AirQualityModule`, implement required hooks (`_run_impl`, reporting builders, config validation) (Sec. 7).
- Performance: Core logic implemented in `air_quality.stats_analysis.core` using Polars expressions and groupby; avoid Python loops; 100k-row perf smoke tests (Sec. 11).
- Units & provenance: Trends require units (Sec. 15). Correlation requires units by default but supports explicit override recorded in provenance. `run()` attaches provenance including config hash, methods, thresholds, time bounds (Sec. 15).
- Reporting: Dashboard payload includes `schema_version`, metrics, counts, flags; CLI text summarizes inputs, methods, QC exclusions, key results, time bounds (Sec. 8).
- Testing/benchmarks: Regression tests for numerics (compare against NumPy/SciPy for small cases), grouped cases, QC filtering, and performance smoke tests (Sec. 10, 11).
- EJ/health/ethics: Core stats only; no sensitive fields; transparent QC handling and caveats (Sec. 6).

## Project Structure

### Documentation (this feature)

```text
specs/003-stats-core/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output (decisions, rationale, alternatives)
├── data-model.md        # Phase 1 output (entities, validation)
├── quickstart.md        # Phase 1 output (usage examples)
└── contracts/
    └── python_api.md    # Phase 1 output (public APIs for primitives/modules)
```

### Source Code (repository root)

```text
src/air_quality/
├── stats_analysis/
│   └── core/
│       ├── descriptive.py    # vectorized stats primitives
│       ├── correlation.py    # pairwise correlation primitives
│       └── trend.py          # linear trend primitives (calendar-aware units)
├── modules/
│   ├── descriptive_stats.py  # AirQualityModule orchestrator
│   ├── correlation.py        # AirQualityModule orchestrator
│   └── trend.py              # AirQualityModule orchestrator
└── (reuse existing)
    ├── module.py             # AirQualityModule base
    ├── dataset/time_series.py# canonical dataset
    ├── units.py              # units registry
    └── time_utils.py         # time bounds/utilities

tests/
├── unit/stats_core/
│   ├── test_descriptive.py
│   ├── test_correlation.py
│   └── test_trend.py
├── integration/modules/
│   ├── test_descriptive_module.py
│   ├── test_correlation_module.py
│   └── test_trend_module.py
└── perf_smoke/
    ├── test_perf_descriptive.py
    ├── test_perf_correlation.py
    └── test_perf_trend.py
```

**Structure Decision**: Single-library project. Add `stats_analysis/core` for DRY primitives; implement thin `modules/*` orchestrators that adhere to `AirQualityModule`. Tests organized by unit/integration/perf.

## Complexity Tracking

No violations anticipated.
