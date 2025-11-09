"""air_quality.dataset.time_series

Time series dataset implementation with datetime index validation.

Constitution compliance:
- Section 3: Mandatory canonical columns (datetime, site_id, pollutant, conc)
- Section 3: Time standards (UTC storage, timezone metadata)
- Section 5: QC validation (time index presence enforced)
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

import pandas as pd
import polars as pl
import pyarrow as pa

from ..exceptions import SchemaError
from ..units import Unit, validate_units_schema
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
        column_units: Optional[Dict[str, Union[Unit, str]]] = None,
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
        column_units : dict[str, Unit | str], optional
            Column name to unit mapping. String values will be normalized
            to Unit enum members via validate_units_schema().

        Raises
        ------
        SchemaError
            If time index column is missing from schema.
        UnitError
            If column_units contains invalid unit strings; error includes
            offending column name.
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

        # Initialize metadata if not provided
        if metadata is None:
            metadata = {}

        # Validate and normalize column_units if provided (Constitution Sec 3)
        if column_units is not None:
            # Use validate_units_schema for normalization and validation
            # Raises UnitError with column name context if invalid
            normalized_units = validate_units_schema(column_units)
            metadata["column_units"] = normalized_units

        super().__init__(data=data, metadata=metadata, mapping=mapping)
        self._time_index_name = time_index_name

    @property
    def time_index_name(self) -> str:
        """Name of the time index column."""
        return self._time_index_name

    @property
    def column_units(self) -> Optional[Dict[str, Unit]]:
        """Column-to-unit mapping if provided at construction.

        Returns None if no unit metadata was specified.

        Constitution Section 3: Unit metadata exposure for provenance.
        Constitution Section 15: Centralized unit validation.

        Returns
        -------
        dict[str, Unit] | None
            Normalized column units mapping, or None if not provided.

        Examples
        --------
        >>> import pandas as pd
        >>> from air_quality.units import Unit
        >>> df = pd.DataFrame({
        ...     'datetime': pd.date_range('2024-01-01', periods=3, freq='h'),
        ...     'site_id': ['A'] * 3,
        ...     'pollutant': ['PM2.5'] * 3,
        ...     'conc': [10.0, 12.0, 14.0]
        ... })
        >>> dataset = TimeSeriesDataset.from_dataframe(
        ...     df, column_units={'conc': 'ug/m3'}
        ... )
        >>> dataset.column_units
        {'conc': <Unit.UG_M3: 'ug/m3'>}
        """
        return self.metadata.get("column_units")

    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        metadata: Optional[Dict[str, Any]] = None,
        mapping: Optional[Dict[str, str]] = None,
        time_index_name: str = "datetime",
        column_units: Optional[Dict[str, Union[Unit, str]]] = None,
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
        column_units : dict[str, Unit | str], optional
            Column name to unit mapping. String values will be normalized
            to Unit enum members.

        Returns
        -------
        TimeSeriesDataset
            Constructed dataset instance.

        Raises
        ------
        SchemaError
            If time index column is missing.
        UnitError
            If column_units contains invalid unit strings.
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
            column_units=column_units,
        )

    @classmethod
    def from_arrow(
        cls,
        table: pa.Table,
        metadata: Optional[Dict[str, Any]] = None,
        mapping: Optional[Dict[str, str]] = None,
        time_index_name: str = "datetime",
        column_units: Optional[Dict[str, Union[Unit, str]]] = None,
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
        column_units : dict[str, Unit | str], optional
            Column name to unit mapping. String values will be normalized
            to Unit enum members.

        Returns
        -------
        TimeSeriesDataset
            Constructed dataset instance.

        Raises
        ------
        SchemaError
            If time index column is missing.
        UnitError
            If column_units contains invalid unit strings.
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
            column_units=column_units,
        )
