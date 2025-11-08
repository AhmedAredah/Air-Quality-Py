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

**Current Status**: 73 tests passing (exceptions, logging, provenance, mapping, dataset, module lifecycle, performance)

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
- `tests/`: Test suite (73 tests covering exceptions, logging, provenance, mapping, dataset, module lifecycle, performance)
- `specs/001-core-foundation/`: Specification documents (tasks.md, quickstart.md)

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Roadmap

- **Phase 9** (current): Documentation finalization
- **Phase 10**: Quality gates & v0.1.0 release
- **Future**: Domain-specific modules (PM2.5 aggregation, AQI calculation, regulatory compliance)
