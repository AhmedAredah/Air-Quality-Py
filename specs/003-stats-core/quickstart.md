# Quickstart – Feature 003: Core Statistical Analysis

This guide shows how to use the statistical analysis modules with a canonical time-series dataset.

## Sample setup

```python
import pandas as pd
from air_quality.modules.statistics.descriptive import (
    DescriptiveStatsModule,
    DescriptiveStatsConfig,
)
from air_quality.qc_flags import QCFlag

# Example canonical long data
df = pd.DataFrame({
    "datetime": pd.date_range("2025-01-01", periods=100, freq="h"),
    "site_id": ["Site_A"] * 50 + ["Site_B"] * 50,
    "pollutant": ["PM25"] * 50 + ["NO2"] * 50,
    "conc": list(range(1, 101)),
    "flag": [QCFlag.VALID.value] * 90 + [QCFlag.INVALID.value] * 10,
})
```

## User Story 1: Descriptive Statistics (MVP - Phase 3 ✓ Implemented)

### Basic Usage - Global Statistics

Compute descriptive statistics across all data (no grouping):

```python
# Create module from dataframe (no grouping)
module = DescriptiveStatsModule.from_dataframe(df, config={})

# Run analysis
module.run()

# Get CLI report
print(module.report_cli())

# Access results programmatically
stats_df = module.results[module.ResultKey.STATISTICS]
print(stats_df)  # Polars DataFrame with tidy format
```

### Grouped Statistics

Compute statistics per site:

```python
# Group by site_id
module = DescriptiveStatsModule.from_dataframe(
    df,
    config={DescriptiveStatsConfig.GROUP_BY: ["site_id"]},
)
module.run()
print(module.report_cli())
```

### Custom Quantiles

Specify custom quantile levels:

```python
# Custom quantiles (10th, 50th, 90th percentiles)
module = DescriptiveStatsModule.from_dataframe(
    df,
    config={DescriptiveStatsConfig.QUANTILES: (0.1, 0.5, 0.9)},
)
module.run()
```

### Dashboard Payload

Get structured JSON-serializable output for dashboards:

```python
dashboard = module.report_dashboard()
print(dashboard.keys())  # dict_keys(['module', 'domain', 'schema_version', 'provenance', 'metrics'])

# Metrics include:
# - statistics: list of dicts (tidy format)
# - n_total, n_valid, n_missing: QC summary
# - time_bounds: {start, end}
```

### Results Structure

The module returns a tidy dataframe with one row per statistic:

```python
# Columns in statistics DataFrame:
# - pollutant: pollutant identifier
# - stat: statistic type (mean, median, std, min, max, q05, q25, q75, q95)
# - value: computed statistic value
# - n_total: total observations before filtering
# - n_valid: valid observations used in computation
# - n_missing: missing observations (excluded + below_dl)
# Plus any grouping columns if group_by was specified
```

## User Story 2: Correlations (Phase 4 - Not Yet Implemented)

```python
# Correlation across pollutants (coming in Phase 4)
# from air_quality.modules.statistics.correlation import CorrelationModule
# mod_corr = CorrelationModule.from_dataframe(df, config={"method": "pearson"})
# res_corr = mod_corr.run()
# print(mod_corr.report_cli())
```

## User Story 3: Trends (Phase 5 - Not Yet Implemented)

```python
# Trend per day for PM25 (coming in Phase 5)
# from air_quality.modules.statistics.trend import TrendModule
# mod_trend = TrendModule.from_dataframe(df, config={"time_unit": "day"})
# res_trend = mod_trend.run()
# print(mod_trend.report_cli())
```

## Notes

- **Input Requirements**: Data must be canonicalizable to `TimeSeriesDataset` (datetime, site_id, pollutant, conc, optional flag).
- **QC Filtering**: Flags `INVALID`/`OUTLIER` are excluded; `BELOW_DL` is treated as missing; null flags treated as `VALID`.
- **Provenance**: All modules automatically attach provenance (config hash, run timestamp, time bounds).
- **Output Format**: Statistics use tidy format (one row per statistic) for easy filtering and visualization.
- **Type Safety**: All configuration uses Enum-based keys for type-safe access.

## See Also

- **Module Implementation**: `src/air_quality/modules/statistics/descriptive.py`
- **Primitive Functions**: `src/air_quality/analysis/descriptive.py`
- **Unit Tests**: `tests/unit/statistics/test_descriptive_*.py`
- **Integration Tests**: `tests/integration/modules/test_descriptive_module_cli.py`

