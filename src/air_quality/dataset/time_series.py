"""air_quality.dataset.time_series

Time series dataset implementation with datetime index validation.

Constitution compliance:
- Section 3: Mandatory canonical columns (datetime, site_id, pollutant, conc)
- Section 3: Time standards (UTC storage, timezone metadata)
- Section 5: QC validation (time index presence enforced)
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import polars as pl
import pyarrow as pa

from ..exceptions import SchemaError
from .base import BaseDataset


class TimeSeriesDataset(BaseDataset):
    """Time series dataset with validated time index.

    Enforces presence of a time index canonical field (typically 'datetime').

    Required Canonical Columns
    ---------------------------
    - datetime : timestamp column
    - site_id : site identifier
    - pollutant or species_id : pollutant/species identifier
    - conc : concentration value

    Optional Canonical Columns
    ---------------------------
    - unc : uncertainty
    - flag : quality flag

    Attributes
    ----------
    time_index_name : str
        Name of the time index column (default: 'datetime').

    Constitution References
    -------
    - Section 3: Data & Metadata Standards (time series canonical columns)
    - Section 5: Quality Control (time index validation)

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({
    ...     'datetime': pd.date_range('2024-01-01', periods=10, freq='h'),
    ...     'site_id': ['A'] * 10,
    ...     'pollutant': ['PM2.5'] * 10,
    ...     'conc': range(10)
    ... })
    >>> dataset = TimeSeriesDataset.from_dataframe(df)
    >>> dataset.time_index_name
    'datetime'
    >>> dataset.n_rows
    10
    """

    def __init__(
        self,
        data: pl.LazyFrame,
        metadata: Optional[Dict[str, Any]] = None,
        mapping: Optional[Dict[str, str]] = None,
        time_index_name: str = "datetime",
    ):
        """Initialize time series dataset.

        Parameters
        ----------
        data : pl.LazyFrame
            Columnar data storage.
        metadata : dict, optional
            Additional metadata.
        mapping : dict[str, str], optional
            Canonical to original column mapping.
        time_index_name : str, default='datetime'
            Name of the time index column.

        Raises
        ------
        SchemaError
            If time index column is missing from schema.
        DataValidationError
            If dataset is empty (via parent class).
        """
        # Validate time index presence before calling parent
        schema = data.collect_schema()
        if time_index_name not in schema.names():
            raise SchemaError(
                f"Time series dataset requires '{time_index_name}' column. "
                f"Available columns: {list(schema.names())}"
            )

        super().__init__(data=data, metadata=metadata, mapping=mapping)
        self._time_index_name = time_index_name

    @property
    def time_index_name(self) -> str:
        """Name of the time index column."""
        return self._time_index_name

    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        metadata: Optional[Dict[str, Any]] = None,
        mapping: Optional[Dict[str, str]] = None,
        time_index_name: str = "datetime",
    ) -> TimeSeriesDataset:
        """Construct time series dataset from pandas DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            Input data with canonical column names.
        metadata : dict, optional
            Additional metadata.
        mapping : dict[str, str], optional
            Canonical to original column mapping.
        time_index_name : str, default='datetime'
            Name of the time index column.

        Returns
        -------
        TimeSeriesDataset
            Constructed dataset instance.

        Raises
        ------
        SchemaError
            If time index column is missing.
        DataValidationError
            If dataset is empty.
        """
        # Convert pandas -> Polars LazyFrame (columnar-first)
        lazy_df = pl.LazyFrame(df)

        return cls(
            data=lazy_df,
            metadata=metadata,
            mapping=mapping,
            time_index_name=time_index_name,
        )

    @classmethod
    def from_arrow(
        cls,
        table: pa.Table,
        metadata: Optional[Dict[str, Any]] = None,
        mapping: Optional[Dict[str, str]] = None,
        time_index_name: str = "datetime",
    ) -> TimeSeriesDataset:
        """Construct time series dataset from PyArrow Table.

        Parameters
        ----------
        table : pa.Table
            Input data with canonical column names.
        metadata : dict, optional
            Additional metadata.
        mapping : dict[str, str], optional
            Canonical to original column mapping.
        time_index_name : str, default='datetime'
            Name of the time index column.

        Returns
        -------
        TimeSeriesDataset
            Constructed dataset instance.

        Raises
        ------
        SchemaError
            If time index column is missing.
        DataValidationError
            If dataset is empty.
        """
        # Convert Arrow -> Polars LazyFrame (columnar-first)
        lazy_df = pl.LazyFrame(table)

        return cls(
            data=lazy_df,
            metadata=metadata,
            mapping=mapping,
            time_index_name=time_index_name,
        )
