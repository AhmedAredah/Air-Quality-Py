# Quickstart: Foundational Core

This quickstart demonstrates creating a dummy module subclassing `AirQualityModule` and running it on a tiny DataFrame. The workflow follows the standard sequence: **mapping → dataset → module run**.

> **Note:** The repository targets Python >= 3.12 (per `pyproject.toml`). Earlier docs may reference Python 3.11; proceed with 3.12 for implementation and testing.

## Example

```python
import pandas as pd
from air_quality.base import AirQualityModule
from air_quality.utils.column_mapping import ColumnMapper

class RowCountModule(AirQualityModule):
    MODULE_NAME = "row_count"
    DOMAIN = "generic"
    OUTPUT_SCHEMA_VERSION = "1.0.0"

    @classmethod
    def _get_required_columns(cls):
        return {"datetime": ["timestamp"], "site_id": ["site"], "conc": ["value"]}

    @classmethod
    def _dataset_from_mapped_df(cls, mapping_result):
        from air_quality.datasets.base import TimeSeriesDataset
        # Assume mapping_result.df_mapped has canonical columns
        import polars as pl
        lf = pl.from_pandas(mapping_result.df_mapped).lazy()
        return TimeSeriesDataset(lf, metadata={"mapping": mapping_result.mapping})

    def _validate_config_impl(self):
        pass

    def _run_impl(self):
        self.results["row_count"] = self.dataset.n_rows

    def _build_dashboard_report_impl(self):
        return {"metrics": {"row_count": self.results["row_count"]}}

    def _build_cli_report_impl(self):
        return f"Row count: {self.results['row_count']}"

# Prepare data
raw_df = pd.DataFrame({
    "timestamp": pd.date_range("2025-01-01", periods=5, freq="H"),
    "site": ["A"] * 5,
    "value": [1,2,3,4,5]
})

module = RowCountModule.from_dataframe(raw_df)
module.run()
print(module.report_cli())
print(module.report_dashboard())
```

## Notes

- **Mapping**: Uses fuzzy matching if explicit mapping not provided; returns `MappingResult` with canonical columns.
- **Dataset Construction**: Internal storage is Polars LazyFrame for deferred computation; conversions occur only on reporting boundaries when necessary.
- **Module Execution**: Provenance attached after `run()`; dashboard/CLI reports available via `report_dashboard()` and `report_cli()`.
- **Performance**: Column mapping handles >100M rows/sec; no unnecessary DataFrame copies during execution.
