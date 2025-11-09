# Quickstart – Feature 003: Core Statistical Analysis

This guide shows how the upcoming modules will be used with a canonical time-series dataset.

## Sample setup

```python
import pandas as pd
from air_quality.modules.descriptive_stats import DescriptiveStatsModule
from air_quality.modules.correlation import CorrelationModule
from air_quality.modules.trend import TrendModule

# Example canonical long data
df = pd.DataFrame({
    "datetime": pd.date_range("2025-01-01", periods=48, freq="h"),
    "site_id": ["S1"]*48,
    "pollutant": ["PM25"]*24 + ["NO2"]*24,
    "conc": list(range(24)) + list(range(24)),
    "flag": [None]*48,
})

# Descriptives by site
mod_desc = DescriptiveStatsModule.from_dataframe(df, mapping={})
res_desc = mod_desc.run()
print(mod_desc.report_cli())

# Correlation across pollutants
mod_corr = CorrelationModule.from_dataframe(df, mapping={}, config={"method":"pearson"})
res_corr = mod_corr.run()
print(mod_corr.report_cli())

# Trend per day for PM25
mod_trend = TrendModule.from_dataframe(df, mapping={}, config={"time_unit":"day"})
res_trend = mod_trend.run()
print(mod_trend.report_cli())
```

Notes:

- Inputs must be canonicalizable to `TimeSeriesDataset` (datetime, site_id, pollutant/species_id, conc, optional unc, flag).
- Flags `invalid`/`outlier` are excluded; `below_dl` is treated as missing.
- Trends require unit metadata for target pollutant.
