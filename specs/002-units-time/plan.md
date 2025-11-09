# Implementation Plan: Feature 002 — Units & Time Primitives (Enum-Based)

**Branch**: `002-units-time` | **Date**: 2025-11-08 | **Spec**: specs/002-units-time/spec.md
**Input**: Feature specification from `/specs/002-units-time/spec.md`

## Summary

### Scope

Provide Enum-based units primitives and time utilities with:

- Central units registry (per-unit defaults; optional per-pollutant rounding overrides).
- Deterministic conversions among ug/m3, mg/m3, ppm, ppb (vectorized; no row loops).
- Reporting rounding via centralized policy.
- Time utilities: UTC-aware time bounds (preserve sub-second precision), pandas-based resampling (boundary), centered rolling mean.
- Dataset integration: strict validation of `column_units` (fail-fast UnitError includes column name).

No implementation occurs in this phase; this plan produces research, data model, API contracts, and quickstart.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Polars, pandas, PyArrow, pytest, mypy (stubs: pandas-stubs, pyarrow-stubs)
**Storage**: Columnar in-memory via Polars LazyFrame; Arrow interchange at boundaries
**Testing**: pytest; mypy static type checking
**Target Platform**: Cross-platform (dev on Windows), CI-ready
**Project Type**: Python library (single repo; src/air_quality)
**Performance Goals**: Conversion of 1M values < 50 ms (smoke), single collect in time bounds, fully vectorized operations
**Constraints**: Columnar-first (Sec 3, 11); no Python row loops; immutability for utilities; no new runtime deps beyond stack
**Scale/Scope**: Millions of rows typical; multiple sites; sub-second timestamps supported

## Constitution Check

GATE status: PASS (design aligned with spec and constitution). Re-evaluated after Phase 1 artifacts; no violations found.

- Data schema & mapping: No ad-hoc mapping introduced. Dataset integration preserves mapping metadata; reuses centralized ColumnMapper (unchanged).
- Architecture: Shared utilities (units/time) are centralized; future modules continue to inherit from `AirQualityModule` (no changes required).
- Performance: Vectorized multiplications only; Polars aggregation for bounds; pandas only at boundary resampling; no row-wise Python loops.
- Units & provenance: Central units registry; rounding policy centralized; ready for downstream provenance attachment by modules.
- Reporting: Rounding policy supports consistent metrics presentation; modules will include units and provenance in dashboard/CLI.
- Testing/benchmarks: Plan includes unit tests for conversions, rounding policy precedence, bounds precision, resampling immutability, and error messages.
- EJ/health/ethics: N/A for this foundational utility; no sensitive data added; policies remain consistent with Sec 6.

Re-check after Phase 1 design: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/002-units-time/
├── plan.md          # This file
├── research.md      # Phase 0 output
├── data-model.md    # Phase 1 output
├── quickstart.md    # Phase 1 output
└── contracts/       # Phase 1 output (units_api.md, time_utils_api.md)
```

### Source Code (repository root)

```text
src/
└── air_quality/
    ├── dataset/
    ├── modules/
    ├── mapping.py
    ├── module.py
    ├── exceptions.py
    └── [future] units.py, time_utils.py  # to be added in implementation phase

tests/
└── [future] test_units_*.py, test_time_*.py
```

**Structure Decision**: Single Python library; shared utilities in `src/air_quality/` to enforce DRY and centralization.

## Complexity Tracking

None.
