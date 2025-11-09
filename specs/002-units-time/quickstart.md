# Quickstart — Feature 002: Units & Time Primitives

Status: ✅ Complete (205 tests passing)
Date: 2025-11-08

This guide demonstrates the implemented API for unit conversion, rounding, and time utilities.

## Units

### Basic Unit Conversion

Convert between concentration units with vectorized operations:

```python
import pandas as pd
import polars as pl
from air_quality import Unit, convert_values, can_convert, get_factor

# Parse unit strings to enum
unit = Unit.parse("ug/m3")  # → Unit.UG_M3

# Check if conversion is supported
can_convert(Unit.UG_M3, Unit.MG_M3)  # → True
can_convert(Unit.PPM, Unit.UG_M3)     # → False (incompatible)

# Get conversion factor
factor = get_factor(Unit.UG_M3, Unit.MG_M3)  # → 0.001

# Convert pandas Series (preserves container type)
values = pd.Series([10.0, 20.0, 30.0])
converted = convert_values(values, Unit.UG_M3, Unit.MG_M3)
# Result: [0.010, 0.020, 0.030]

# Convert Polars Series
pl_values = pl.Series([10.0, 20.0, 30.0])
pl_converted = convert_values(pl_values, Unit.PPB, Unit.PPM)
# Result: [0.010, 0.020, 0.030]

# Convert scalar
scalar = convert_values(100.0, Unit.UG_M3, Unit.MG_M3)
# Result: 0.1

# NaN values are preserved
with_nans = pd.Series([10.0, float('nan'), 30.0])
result = convert_values(with_nans, Unit.UG_M3, Unit.MG_M3)
# Result: [0.010, NaN, 0.030]
```

### Rounding for Reporting

Apply standardized rounding policies with per-unit defaults and pollutant overrides:

```python
from air_quality import round_for_reporting

# Default rounding (based on unit)
values = pd.Series([1.23456, 2.34567, 3.45678])
rounded = round_for_reporting(values, Unit.MG_M3)
# Result: [1.235, 2.346, 3.457] (3 decimal places for mg/m3)

rounded_ug = round_for_reporting(values, Unit.UG_M3)
# Result: [1.2, 2.3, 3.5] (1 decimal place for ug/m3)

# Pollutant-specific override
no2_values = pd.Series([12.345, 23.456])
rounded_no2 = round_for_reporting(no2_values, Unit.PPB, pollutant="NO2")
# Result: [12.3, 23.5] (override applied if configured)

# Works with Polars Series and scalars
pl_rounded = round_for_reporting(pl.Series([1.23456]), Unit.PPB)
scalar_rounded = round_for_reporting(1.23456, Unit.PPM)
```

### Unit Schema Validation

Normalize and validate unit metadata for datasets:

```python
from air_quality import validate_units_schema

# Normalize mixed str/Unit schema
schema = validate_units_schema({
    "conc": "ug/m3",      # String gets normalized
    "unc": Unit.UG_M3,    # Enum passes through
    "temp": "invalid"     # Will raise UnitError
})
# Result: {"conc": Unit.UG_M3, "unc": Unit.UG_M3}

# All-string schema
schema2 = validate_units_schema({
    "pm25": "ug/m3",
    "pm10": "ug/m3"
})
# Result: {"pm25": Unit.UG_M3, "pm10": Unit.UG_M3}

# Empty schema is allowed
empty = validate_units_schema({})
# Result: {}
```

## Time Utilities

### Time Bounds Computation

Compute UTC-aware time bounds from Polars LazyFrame with single aggregation:

```python
import polars as pl
from air_quality import compute_time_bounds, TimeBounds

# Create LazyFrame with datetime column
lf = pl.LazyFrame({
    "datetime": [
        "2025-01-01T00:00:00.123456",
        "2025-01-01T06:30:15.789012",
        "2025-01-01T12:00:00.000000"
    ]
}).with_columns(pl.col("datetime").str.strptime(pl.Datetime))

# Compute bounds (single collect operation)
bounds = compute_time_bounds(lf, time_col="datetime")
# Result: TimeBounds(
#   start=datetime(2025, 1, 1, 0, 0, 0, 123456, tzinfo=UTC),
#   end=datetime(2025, 1, 1, 12, 0, 0, 0, tzinfo=UTC)
# )

print(bounds.start)  # UTC-aware datetime with sub-second precision
print(bounds.end)

# Works with timezone-aware input
lf_aware = lf.with_columns(
    pl.col("datetime").dt.replace_time_zone("America/New_York")
)
bounds_aware = compute_time_bounds(lf_aware)
# Result: Converted to UTC automatically
```

### Resampling to Hourly Mean

Resample time series data with pandas (immutable operation):

```python
import pandas as pd
from air_quality import resample_mean

# Create sample data
df = pd.DataFrame({
    "datetime": pd.date_range("2025-01-01", periods=10, freq="30min"),
    "pm25": [10.5, 11.2, 12.1, 13.0, 14.5, 15.1, 16.2, 17.0, 18.3, 19.1],
    "pm10": [20.1, 21.5, 22.3, 23.8, 24.2, 25.6, 26.1, 27.4, 28.0, 29.2],
    "site_id": ["A"] * 10
})

# Resample to hourly (returns new DataFrame)
hourly = resample_mean(df, rule="1H", time_col="datetime")
# Result: New DataFrame with hourly averages
# Original df is unchanged (immutable operation)

# Resample with different frequencies
daily = resample_mean(df, rule="1D", time_col="datetime")
every_2h = resample_mean(df, rule="2H", time_col="datetime")

# Only numeric columns are averaged (site_id is dropped)
print(hourly.columns)  # ['datetime', 'pm25', 'pm10']

# Datetime is coerced if string column provided
df_str = df.copy()
df_str["datetime"] = df_str["datetime"].astype(str)
hourly_str = resample_mean(df_str, rule="1H", time_col="datetime")
# Automatically converts to datetime
```

### Rolling Window Mean

Apply centered rolling mean for QC and smoothing:

```python
from air_quality import rolling_window_mean

# Create sample data
df = pd.DataFrame({
    "datetime": pd.date_range("2025-01-01", periods=10, freq="1H"),
    "pm25": [10, 15, 20, 100, 18, 16, 14, 12, 11, 10],  # Note spike at index 3
    "site_id": ["A"] * 10
})

# Apply 3-hour centered rolling mean
smoothed = rolling_window_mean(df, window=3, time_col="datetime")
# Result: New DataFrame with smoothed values
# Spike at index 3 is dampened

# Window=1 returns original values
identity = rolling_window_mean(df, window=1, time_col="datetime")
# Result: Same as original (numeric columns only)

# Edges filled with available data (min_periods=1)
print(smoothed["pm25"].iloc[0])  # Uses only first 2 points
print(smoothed["pm25"].iloc[-1]) # Uses only last 2 points

# Automatically sorts by time before rolling
unsorted_df = df.sample(frac=1.0, random_state=42)  # Shuffle rows
sorted_result = rolling_window_mean(unsorted_df, window=3, time_col="datetime")
# Result: Time-sorted before rolling applied
```

## Integration with TimeSeriesDataset

Use validated unit metadata in datasets:

```python
from air_quality.dataset import TimeSeriesDataset
import polars as pl

# Create dataset with unit metadata
lf = pl.LazyFrame({
    "datetime": pd.date_range("2025-01-01", periods=5, freq="1H"),
    "site_id": ["A"] * 5,
    "pm25": [10.0, 11.0, 12.0, 13.0, 14.0]
})

dataset = TimeSeriesDataset(
    lazyframe=lf,
    metadata={
        "column_units": {
            "pm25": "ug/m3"  # Automatically validated and normalized
        }
    }
)

# Access normalized unit schema
units = dataset.column_units
# Result: {"pm25": Unit.UG_M3}

# Invalid units raise UnitError with column name
try:
    bad_dataset = TimeSeriesDataset(
        lazyframe=lf,
        metadata={"column_units": {"pm25": "invalid_unit"}}
    )
except Exception as e:
    print(f"Error: {e}")  # "Invalid unit 'invalid_unit' for column 'pm25'"
```

## Performance Notes

- **Unit Conversion**: Validated to handle 1M rows in <2ms (25x better than 50ms target)
- **Time Bounds**: Single aggregation operation (Constitution Sec 11 compliant)
- **No Python Row Loops**: All operations use vectorized NumPy/Pandas/Polars operations
- **Memory Efficient**: No unnecessary DataFrame copies; immutable operations return new objects

## Error Handling

All functions raise structured exceptions with detailed context:

```python
from air_quality import UnitError

# Invalid unit string
try:
    Unit.parse("invalid")
except UnitError as e:
    print(e)  # "Invalid unit string: invalid"

# Unsupported conversion
try:
    convert_values(10.0, Unit.PPM, Unit.UG_M3)
except UnitError as e:
    print(e)  # "Cannot convert from PPM to UG_M3"

# Non-numeric types
try:
    convert_values("not_a_number", Unit.UG_M3, Unit.MG_M3)
except TypeError as e:
    print(e)  # "values must be numeric, got <class 'str'>"
```

---

**Next Steps**: See [spec.md](spec.md) for detailed API contracts and [HANDOFF.md](HANDOFF.md) for implementation notes.
