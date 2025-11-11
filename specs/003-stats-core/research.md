# Research – Feature 003: Core Statistical Analysis

## Decisions

1. Columnar backend: Polars for core primitives; Pandas only for boundary helpers

- Rationale: Polars provides fast, expressive groupby/agg with lazy evaluation; aligns with Constitution Sec. 11 (vectorized, columnar). Pandas retained for resampling utilities already present in `time_utils`.
- Alternatives: Pandas-only (simpler API but slower for large data); PySpark/Dask (overkill for local scale; increases complexity).

1. Descriptive statistics primitive

- Rationale: Implement as Polars groupby over canonical long data, computing mean, median, std, min, max, quantiles (5,25,75,95) with counts and QC-aware filters.
- Alternatives: NumPy aggregations on pivoted arrays (requires additional memory); Pandas groupby (slower on 100k+ rows).

1. Correlation primitive (Pearson, Spearman)

- Rationale: Compute per-group pairwise correlations by pivoting to wide within group (temporary) and using vectorized covariance formula for Pearson and rank transform for Spearman. Enforce ordered pairs (x<=y), include diagonal, track n.
- Alternatives: SciPy `pearsonr`/`spearmanr` per pair (looping; slower); NumPy corrcoef over dense arrays (less control over n and masking of pairwise missingness).

1. Trend primitive (conc ~ time)

- Rationale: Closed-form OLS slope/intercept via sufficient statistics per group with time represented in calendar-aware units (hour/day/calendar_month/calendar_year). Compute elapsed units deterministically; avoid sklearn dependency.
- Alternatives: Statsmodels/Scikit-learn (heavier deps; slower; less control over calendar-aware semantics).

1. Units policy

- Rationale: Trends require known units; slopes reported as {Unit} per {time_unit}. Correlation requires unit metadata by default; override allowed and recorded in provenance. Mixed unit families allowed in correlation (scale-invariant); no conversion performed.
- Alternatives: Auto-convert to canonical units (adds hidden behavior; violates explicitness per Constitution Sec. 15).

1. QC flags

- Rationale: Exclude rows flagged `invalid`/`outlier`; treat `below_dl` as missing; report `n_total`, `n_valid`, `n_missing`. Matches Spec FR-005 and Constitution Sec. 3.
- Alternatives: Substitution for below DL (e.g., DL/2); deferred to future explicit imputation modules.

1. Thresholds

- Rationale: `min_samples` default 3 (configurable) for correlation/trend; `min_duration_years` default 1 for trends, configurable. Compute results regardless but flag `low_n`/`short_duration` in module outputs.
- Alternatives: Hard drop results below thresholds (less transparent; reduces utility for sparse datasets).

1. Reporting

- Rationale: Dashboard JSON with `schema_version`, metrics, counts, provenance; CLI text summary. Aligns with Constitution Sec. 8.
- Alternatives: Single reporting channel (CLI only) – rejected by Constitution.

## Open Items (tracked)
- Diagnostics placeholders (p_value, CI) reserved; to be implemented in a later feature (no blocker here).
