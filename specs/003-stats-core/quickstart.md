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

## User Story 2: Correlations (Phase 4 ✓ Implemented)

### Basic Usage - Pearson Correlation

Compute pairwise correlations across pollutants:

```python
from air_quality.modules.statistics.correlation import (
    CorrelationModule,
    CorrelationConfig,
)
from air_quality.analysis.correlation import CorrelationMethod

# Create module from dataframe
module = CorrelationModule.from_dataframe(
    df,
    config={
        CorrelationConfig.METHOD: CorrelationMethod.PEARSON,
        CorrelationConfig.CATEGORY_COL: "pollutant",
        CorrelationConfig.VALUE_COL: "conc",
        CorrelationConfig.FLAG_COL: "flag",
    },
)

# Run analysis
module.run()

# Get CLI report (includes correlation matrix)
print(module.report_cli())

# Access results programmatically
corr_df = module.results[module.ResultKey.CORRELATIONS]
print(corr_df)  # Polars DataFrame with ordered pairs
```

### Spearman Correlation

Use rank-based correlation for non-linear relationships:

```python
module = CorrelationModule.from_dataframe(
    df,
    config={
        CorrelationConfig.METHOD: CorrelationMethod.SPEARMAN,
        CorrelationConfig.CATEGORY_COL: "pollutant",
        CorrelationConfig.VALUE_COL: "conc",
    },
)
module.run()
```

### Grouped Correlations

Compute correlations separately for each site:

```python
module = CorrelationModule.from_dataframe(
    df,
    config={
        CorrelationConfig.METHOD: CorrelationMethod.PEARSON,
        CorrelationConfig.GROUP_BY: ["site_id"],
        CorrelationConfig.CATEGORY_COL: "pollutant",
        CorrelationConfig.VALUE_COL: "conc",
    },
)
module.run()
# Results will have one set of correlations per site
```

### Results Structure

The module returns ordered unique pairs with correlation coefficients:

```python
# Columns in correlations DataFrame:
# - var_x, var_y: pollutant pair (var_x <= var_y lexicographically)
# - correlation: Pearson r or Spearman rho
# - n: number of valid pairwise observations
# Plus any grouping columns if group_by was specified
```

## User Story 3: Trends (Phase 5 ✓ Implemented)

### Basic Usage - Linear Trend

Compute linear trends over time with calendar-aware units:

```python
from air_quality.modules.statistics.trend import (
    TrendModule,
    TrendConfig,
)
from air_quality.units import TimeUnit

# Create module from dataframe
module = TrendModule.from_dataframe(
    df,
    config={
        TrendConfig.TIME_UNIT: TimeUnit.DAY,
        TrendConfig.POLLUTANT_COL: "pollutant",
        TrendConfig.DATETIME_COL: "datetime",
        TrendConfig.CONC_COL: "conc",
        TrendConfig.FLAG_COL: "flag",
    },
)

# Run analysis
module.run()

# Get CLI report (includes slopes, R², flags)
print(module.report_cli())

# Access results programmatically
trend_df = module.results[module.ResultKey.TRENDS]
print(trend_df)  # Polars DataFrame with trend metrics
```

### Calendar-Aware Time Units

Use calendar-aware time units for long-term trends:

```python
# Trend per calendar year (handles leap years)
module = TrendModule.from_dataframe(
    df,
    config={
        TrendConfig.TIME_UNIT: TimeUnit.CALENDAR_YEAR,
        TrendConfig.POLLUTANT_COL: "pollutant",
        TrendConfig.DATETIME_COL: "datetime",
        TrendConfig.CONC_COL: "conc",
    },
)
module.run()
```

### Grouped Trends

Compute trends separately for each site:

```python
module = TrendModule.from_dataframe(
    df,
    config={
        TrendConfig.TIME_UNIT: TimeUnit.DAY,
        TrendConfig.GROUP_BY: ["site_id"],
        TrendConfig.POLLUTANT_COL: "pollutant",
        TrendConfig.DATETIME_COL: "datetime",
        TrendConfig.CONC_COL: "conc",
    },
)
module.run()
```

### Custom Thresholds

Adjust minimum sample size and duration thresholds:

```python
module = TrendModule.from_dataframe(
    df,
    config={
        TrendConfig.TIME_UNIT: TimeUnit.DAY,
        TrendConfig.MIN_SAMPLES: 10,  # At least 10 observations
        TrendConfig.MIN_DURATION_YEARS: 0.5,  # At least 6 months
        TrendConfig.POLLUTANT_COL: "pollutant",
        TrendConfig.DATETIME_COL: "datetime",
        TrendConfig.CONC_COL: "conc",
    },
)
module.run()
```

### Results Structure

The module returns OLS regression results with quality flags:

```python
# Columns in trends DataFrame:
# - slope: trend slope (concentration units / time unit)
# - intercept: y-intercept
# - r_squared: coefficient of determination (0-1)
# - n: number of valid observations
# - duration_years: time span in years
# - short_duration_flag: True if duration < min_duration_years
# - low_n_flag: True if n < min_samples
# - slope_units: units of slope (e.g., "ug/m3/day", "ppb/calendar_year")
# Plus any grouping columns if group_by was specified
```

## Notes

- **Input Requirements**: Data must be canonicalizable to `TimeSeriesDataset` (datetime, site_id, pollutant, conc, optional flag).
- **QC Filtering**: Flags `INVALID`/`OUTLIER` are excluded; `BELOW_DL` is treated as missing; null flags treated as `VALID`.
- **Provenance**: All modules automatically attach provenance (config hash, run timestamp, time bounds).
- **Output Format**: Statistics use tidy format (one row per statistic) for easy filtering and visualization.
- **Type Safety**: All configuration uses Enum-based keys for type-safe access.

## See Also

### Module Implementations
- **Descriptive Statistics**: `src/air_quality/modules/statistics/descriptive.py`
- **Correlations**: `src/air_quality/modules/statistics/correlation.py`
- **Trends**: `src/air_quality/modules/statistics/trend.py`

### Primitive Functions
- **Descriptive Primitives**: `src/air_quality/analysis/descriptive.py`
- **Correlation Primitives**: `src/air_quality/analysis/correlation.py`
- **Trend Primitives**: `src/air_quality/analysis/trend.py`

### Test Suites
- **Descriptive Unit Tests**: `tests/unit/statistics/test_descriptive_*.py`
- **Correlation Unit Tests**: `tests/unit/statistics/test_correlation_*.py`
- **Trend Unit Tests**: `tests/unit/statistics/test_trend_*.py`
- **Integration Tests**: `tests/integration/modules/test_*_module_cli.py`
- **Performance Tests**: `tests/perf_smoke/test_perf_*.py`

