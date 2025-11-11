# Data Model – Feature 003: Core Statistical Analysis

## Entities

### StatisticResult (tidy row)

- Keys: group columns..., pollutant
- Fields:
  - stat: one of [mean, median, std, min, max, q05, q25, q75, q95]
  - value: float
  - n_total: int
  - n_valid: int
  - n_missing: int
- Validation:
  - value is finite (NaN only permitted if n_valid=0)
  - counts are consistent: n_total = n_valid + n_missing

### CorrelationResult (tidy row)

- Keys: group columns..., var_x, var_y
- Fields:
  - method: {pearson, spearman}
  - correlation: float in [-1, 1] (NaN if n<2)
  - n: int (pairwise valid count)
  - p_value (optional, reserved)
  - ci_lower, ci_upper (optional, reserved)
- Validation:
  - var_x <= var_y (ordered pair canonicalization)

### TrendResult (tidy row)

- Keys: group columns..., pollutant
- Fields:
  - time_unit: {hour, day, calendar_month, calendar_year}
  - slope: float (Unit per time_unit)
  - intercept: float (Unit at reference = 0)
  - n: int (valid observations used)
  - short_duration_flag: bool (if duration < min_duration_years)
  - r2, p_value, slope_se, ci_lower, ci_upper, resid_var (optional, reserved)
- Validation:
  - Units present for pollutant (raise UnitError otherwise)
  - Duration computed from bounds; provenance includes bounds and duration

## Relationships

- Each result row maps back to a `TimeSeriesDataset` slice defined by grouping keys and pollutant selection.
- Provenance records include module name, domain, config hash, methods, thresholds, time bounds, units status.
