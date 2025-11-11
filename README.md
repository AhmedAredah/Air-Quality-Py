# air-quality

**Modular air quality data analysis framework with rigorous provenance tracking.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

`air-quality` provides a **foundational core** for building reusable, type-safe air quality analysis modules. It emphasizes:

- **Provenance Tracking**: Every module execution generates a deterministic SHA-256 hash from inputs, configuration, code version, and dependencies—ensuring reproducibility and auditability.
- **Column Mapping**: Flexible 3-level resolution (explicit → synonyms → fuzzy) maps arbitrary input DataFrames to canonical schemas with detailed diagnostics.
- **Polars LazyFrame Backend**: Deferred computation and zero-copy conversions minimize memory overhead; validated to handle >100M rows/sec for mapping operations.
- **Structured Reporting**: Modules produce both machine-readable dashboard payloads (JSON-serializable TypedDicts) and human-readable CLI reports.
- **DRY Architecture**: Single `AirQualityModule` base class enforces consistent lifecycle: validate → run → report → provenance.

---

## Installation

**Requirements**: Python >= 3.12

### Using `uv` (recommended)

```bash
uv pip install -e .
```

### Using `pip`

```bash
pip install -e .
```

---

## Quick Start

### Example: RowCountModule

This example demonstrates the standard workflow: **mapping → dataset → module run**.

```python
import pandas as pd
from air_quality.module import AirQualityModule
from air_quality.dataset import TimeSeriesDataset

class RowCountModule(AirQualityModule):
    """Simple module counting rows in a time-series dataset."""
    
    MODULE_NAME = "row_count"
    DOMAIN = "generic"
    OUTPUT_SCHEMA_VERSION = "1.0.0"

    @classmethod
    def _get_required_columns(cls):
        return {
            "datetime": ["timestamp", "time"],
            "site_id": ["site", "location"],
            "conc": ["value", "concentration"]
        }

    def _validate_config_impl(self):
        # No config needed for this module
        pass

    def _run_impl(self):
        # Access dataset via self.dataset (Polars LazyFrame wrapper)
        self.results["row_count"] = len(self.dataset.lazyframe.collect())

    def _build_dashboard_report_impl(self):
        return {"metrics": {"row_count": self.results["row_count"]}}

    def _build_cli_report_impl(self):
        return f"Row count: {self.results['row_count']}"

# Prepare input data (arbitrary column names)
raw_df = pd.DataFrame({
    "timestamp": pd.date_range("2025-01-01", periods=5, freq="H"),
    "site": ["A"] * 5,
    "value": [1, 2, 3, 4, 5]
})

# Run the module (automatically handles mapping → dataset → execution)
module = RowCountModule.from_dataframe(raw_df)
module.run()

# Get results
print(module.report_cli())
# Output: Row count: 5

print(module.report_dashboard())
# Output: {'module': 'row_count', 'domain': 'generic', ...}

# Access provenance
print(module.provenance.provenance_hash)
# Output: sha256:abc123... (deterministic hash)
```

### Units & Time Utilities (Feature 002)

**Status**: ✅ Complete (205 tests passing)

Foundation for unit conversion, rounding policies, and time utilities:

```python
import pandas as pd
import polars as pl
from air_quality import (
    Unit,
    convert_values,
    round_for_reporting,
    validate_units_schema,
    TimeBounds,
    compute_time_bounds,
    resample_mean,
    rolling_window_mean,
)

# Unit conversion (vectorized operations, preserves container type)
Unit.parse("ug/m3")  # → Unit.UG_M3

# Convert pandas Series
values = pd.Series([10.0, 20.0, 30.0])
converted = convert_values(values, Unit.UG_M3, Unit.MG_M3)
# Result: [0.010, 0.020, 0.030] (ug/m3 → mg/m3)

# Centralized rounding for reporting (per-unit defaults + pollutant overrides)
rounded = round_for_reporting(converted, Unit.MG_M3)
# Result: [0.010, 0.020, 0.030] (3 decimal places for mg/m3)

# Validate and normalize unit metadata
schema = validate_units_schema({
    "conc": "ug/m3",      # String gets normalized
    "unc": Unit.UG_M3     # Enum passes through
})
# Result: {"conc": Unit.UG_M3, "unc": Unit.UG_M3}

# Time bounds (Polars LazyFrame → UTC-aware, sub-second precision)
lf = pl.LazyFrame({
    "datetime": [
        "2025-01-01T00:00:00.123456",
        "2025-01-01T01:00:00.789012"
    ]
}).with_columns(pl.col("datetime").str.strptime(pl.Datetime))

bounds = compute_time_bounds(lf, time_col="datetime")
# Result: TimeBounds(start=datetime(..., tzinfo=UTC), end=datetime(..., tzinfo=UTC))
# Single aggregation operation (Constitution Sec 11 compliant)

# Resampling (pandas boundary operation, returns new DataFrame)
df = pd.DataFrame({
    "datetime": pd.date_range("2025-01-01", periods=10, freq="30min"),
    "conc": range(10),
    "site_id": ["A"] * 10
})
hourly = resample_mean(df, rule="1H", time_col="datetime")
# Result: New DataFrame with hourly averages; original df unchanged

# Rolling mean QC helper (centered window, min_periods=1)
smoothed = rolling_window_mean(df, window=3, time_col="datetime")
# Result: New DataFrame with rolling mean applied to numeric columns
```

**Performance**: Validated to handle 1M row conversions in <2ms (25x better than 50ms target). No Python row loops in any function (vectorized operations only).

**Quickstart**: See [specs/002-units-time/quickstart.md](specs/002-units-time/quickstart.md) for detailed examples.

---

### Core Statistical Analysis (Feature 003)

**Status**: ✅ Complete (137+ tests passing)

Modular statistical analysis with descriptive statistics, correlations, and linear trends:

```python
from air_quality.modules.statistics import (
    DescriptiveStatsModule,
    CorrelationModule,
    TrendModule,
)
from air_quality.analysis.correlation import CorrelationMethod
from air_quality.units import TimeUnit

# Sample data (canonical long format)
import pandas as pd
df = pd.DataFrame({
    "datetime": pd.date_range("2025-01-01", periods=100, freq="H"),
    "site_id": ["Site_A"] * 50 + ["Site_B"] * 50,
    "pollutant": ["PM25"] * 50 + ["NO2"] * 50,
    "conc": range(1, 101),
    "flag": ["valid"] * 90 + ["invalid"] * 10,
})

# Descriptive Statistics (tidy or wide format)
module_desc = DescriptiveStatsModule.from_dataframe(
    df,
    config={"group_by": ["site_id"]},
)
module_desc.run()
print(module_desc.report_cli())  # Human-readable table
stats = module_desc.results["statistics"]  # Polars DataFrame

# Correlations (Pearson or Spearman)
module_corr = CorrelationModule.from_dataframe(
    df,
    config={
        "method": CorrelationMethod.PEARSON,
        "category_col": "pollutant",
        "value_col": "conc",
    },
)
module_corr.run()
print(module_corr.report_cli())  # Includes correlation matrix
correlations = module_corr.results["correlations"]

# Linear Trends (calendar-aware time units)
module_trend = TrendModule.from_dataframe(
    df,
    config={
        "time_unit": TimeUnit.DAY,
        "pollutant_col": "pollutant",
        "datetime_col": "datetime",
        "conc_col": "conc",
    },
)
module_trend.run()
print(module_trend.report_cli())  # Slopes, R², quality flags
trends = module_trend.results["trends"]
```

**Key Features**:
- **Lazy Evaluation**: All primitives return Polars LazyFrame for query optimization
- **QC Integration**: Automatic filtering of invalid/outlier flags, below_dl treated as missing
- **Unit Enforcement**: Descriptive stats preserve units; trends compute slope_units (e.g., "ug/m3/day")
- **Calendar-Aware Time**: Trends support hour, day, calendar_month, calendar_year with fractional year computation
- **Performance**: Validated to handle 100k rows in <2s per primitive (closed-form OLS, single-pass aggregations)
- **Output Formats**: Tidy (long) or wide format for descriptive stats; ordered unique pairs for correlations

**Primitives** (in `analysis/` package):
- `compute_descriptives()`: Mean, median, std, min, max, quantiles (5th, 25th, 75th, 95th)
- `compute_pairwise()`: Pearson/Spearman correlation with ordered unique pairs
- `compute_linear_trend()`: OLS regression slope/intercept with duration/sample-size flags

**Modules** (in `modules/statistics/`):
- `DescriptiveStatsModule`: Orchestrates descriptive stats with grouping and QC filtering
- `CorrelationModule`: Pairwise correlations with global/grouped modes
- `TrendModule`: Linear trends with calendar-aware time units and quality flags

**Quickstart**: See [specs/003-stats-core/quickstart.md](specs/003-stats-core/quickstart.md) for comprehensive examples.

---

## Architecture

### Core Components

```text
air_quality/
├── exceptions.py       # Taxonomy: ConfigurationError, DataValidationError, etc.
├── logging.py          # Structured logging with module/domain context
├── provenance.py       # Deterministic hashing of inputs + config + code
├── mapping.py          # 3-level column resolution with fuzzy matching
├── dataset/            # Polars LazyFrame wrappers
│   ├── base.py         # BaseDataset abstract class
│   └── time_series.py  # TimeSeriesDataset with time index enforcement
└── module.py           # AirQualityModule base class
```

### Execution Lifecycle

1. **Mapping**: `ColumnMapper.map()` resolves arbitrary column names to canonical schema
2. **Dataset Construction**: Mapped DataFrame → Polars LazyFrame → TimeSeriesDataset
3. **Configuration Validation**: Module-specific config checks via `_validate_config_impl()`
4. **Execution**: `_run_impl()` operates on `self.dataset` (LazyFrame wrapper)
5. **Provenance Generation**: Deterministic hash from inputs + config + code + dependencies
6. **Reporting**: Dashboard (TypedDict) and CLI (string) outputs via `report_dashboard()` / `report_cli()`

---

## Why Provenance?

Every `run()` execution generates a **provenance hash** capturing:

- **Input data signature**: Hash of DataFrame contents
- **Configuration**: Serialized config dictionary
- **Code version**: Module `OUTPUT_SCHEMA_VERSION` + package version
- **Dependencies**: Locked versions of Polars, pandas, PyArrow

**Benefits:**

- **Reproducibility**: Identical inputs + config + code → identical hash
- **Auditability**: Track which version of code/data produced a result
- **Debugging**: Compare hashes across runs to detect environmental drift
- **Compliance**: Regulatory scenarios requiring analysis lineage

Example provenance object:

```python
{
    "module": "row_count",
    "domain": "generic",
    "schema_version": "1.0.0",
    "timestamp": "2025-01-15T12:34:56Z",
    "provenance_hash": "sha256:abc123...",
    "inputs": {"dataframe_hash": "sha256:def456..."},
    "config": {},
    "runtime": {"python_version": "3.12.0", "polars_version": "0.20.3"}
}
```

---

## Performance

Validated with **1M row benchmarks** (see `tests/test_mapping_perf.py`):

- **Column Mapping**: >100M rows/sec (explicit & fuzzy)
- **Memory**: Zero unnecessary DataFrame copies; LazyFrame deferred computation
- **Scaling**: Linear performance from 10K → 1M rows

---

## Development

### Running Tests

```bash
uv run -q pytest -q
```

**Current Status**: 205 tests passing (exceptions, logging, provenance, mapping, dataset, module lifecycle, units, time utilities, performance)

### Type Checking

**Status**: ✅ Configured with mypy

Type hints are present throughout the codebase with `py.typed` marker included.

Run type checking:

```bash
uv run mypy src/air_quality
```

**Current Status**: All type checks passing (11 source files)

### Versioning Policy

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality additions
- **PATCH**: Backward-compatible bug fixes

Current version: **0.1.0** (initial foundational core release)

### Project Structure

- `src/air_quality/`: Source code
- `tests/`: Test suite (205 tests covering exceptions, logging, provenance, mapping, dataset, module lifecycle, units, time utilities, performance)
- `specs/001-core-foundation/`: Specification documents (tasks.md, quickstart.md)

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Roadmap

- **Phase 9** (current): Documentation finalization
- **Phase 10**: Quality gates & v0.1.0 release
- **Future**: Domain-specific modules (PM2.5 aggregation, AQI calculation, regulatory compliance)
