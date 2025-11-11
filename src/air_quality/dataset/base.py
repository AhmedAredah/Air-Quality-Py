"""air_quality.dataset.base

Abstract base dataset wrapper with Polars LazyFrame backend.

Constitution compliance:
- Columnar-first: Internal storage uses Polars LazyFrame (Section 3, 11)
- Explicit conversions: to_arrow(), to_pandas() at boundaries only (Section 3)
- Metadata preservation: mapping metadata included (Section 3)
- Immutability: Dataset remains immutable except explicit conversions (data-model.md)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import pandas as pd
import polars as pl
import pyarrow as pa

from ..exceptions import DataValidationError


class BaseDataset(ABC):
    """Abstract canonical dataset wrapper.

    Internal storage uses Polars LazyFrame for columnar efficiency.
    Conversions to Arrow/pandas are explicit and occur only at boundaries.

    Attributes
    ----------
    data : pl.LazyFrame
        Internal columnar storage (Polars LazyFrame).
    metadata : dict
        Additional dataset metadata (site info, time ranges, etc.).
    mapping : dict[str, str] | None
        Optional mapping from canonical column names to original column names.

    Properties
    ----------
    lazyframe : pl.LazyFrame
        Access to internal LazyFrame (read-only).
    schema : dict[str, str]
        Column names and their Polars dtypes as strings.
    n_rows : int
        Number of rows (computed, triggers collection).

    Methods
    -------
    is_empty() -> bool
        Check if dataset has zero rows.
    get_column(name: str) -> pl.Series
        Get a specific column by canonical name (triggers collection).
    get_dataset_id() -> str | None
        Retrieve dataset identifier from metadata if available.
    to_arrow() -> pa.Table
        Convert to PyArrow Table for interchange.
    to_pandas() -> pd.DataFrame
        Convert to pandas DataFrame for legacy APIs.

    Constitution References
    -------
    - Section 3: Data & Metadata Standards (columnar backend, mapping preservation)
    - Section 11: Performance, Scalability (LazyFrame for large datasets, no row loops)
    """

    def __init__(
        self,
        data: pl.LazyFrame,
        metadata: Optional[Dict[str, Any]] = None,
        mapping: Optional[Dict[str, str]] = None,
    ):
        """Initialize dataset with Polars LazyFrame.

        Parameters
        ----------
        data : pl.LazyFrame
            Columnar data storage.
        metadata : dict, optional
            Additional metadata (site info, time ranges, provenance details).
        mapping : dict[str, str], optional
            Mapping from canonical column names to original names.

        Raises
        ------
        DataValidationError
            If dataset is empty (zero rows).
        """
        self._data: pl.LazyFrame = data
        self._metadata: Dict[str, Any] = metadata or {}
        self._mapping: Optional[Dict[str, str]] = mapping

        # Validate non-empty (constitution Section 5: QC)
        if self.is_empty():
            raise DataValidationError("Dataset cannot be empty (zero rows)")

    @property
    def lazyframe(self) -> pl.LazyFrame:
        """Access internal LazyFrame storage (read-only)."""
        return self._data

    @property
    def schema(self) -> Dict[str, str]:
        """Column names and their Polars dtypes as strings."""
        return {name: str(dtype) for name, dtype in self._data.collect_schema().items()}

    @property
    def metadata(self) -> Dict[str, Any]:
        """Access dataset metadata (read-only view)."""
        return self._metadata

    @property
    def mapping(self) -> Optional[Dict[str, str]]:
        """Access column mapping metadata (canonical -> original)."""
        return self._mapping

    @property
    def n_rows(self) -> int:
        """Number of rows (triggers collection)."""
        # Note: This collects the LazyFrame; use sparingly
        df = self._data.select(pl.len()).collect()
        return df.item()

    def is_empty(self) -> bool:
        """Check if dataset has zero rows.

        Returns
        -------
        bool
            True if dataset is empty, False otherwise.
        """
        return self.n_rows == 0

    def get_column(self, name: str) -> pl.Series:
        """Get a specific column by canonical name.

        Parameters
        ----------
        name : str
            Canonical column name.

        Returns
        -------
        pl.Series
            The requested column (triggers collection).

        Raises
        ------
        KeyError
            If column name not found in schema.
        """
        if name not in self._data.collect_schema().names():
            raise KeyError(f"Column '{name}' not found in dataset schema")
        return self._data.select(name).collect()[name]

    def get_dataset_id(self) -> Optional[str]:
        """Retrieve dataset identifier from metadata if available.

        Returns
        -------
        str | None
            Dataset ID if present in metadata, otherwise None.
        """
        return self._metadata.get("dataset_id")

    def to_arrow(self) -> pa.Table:
        """Convert to PyArrow Table for interchange.

        Triggers collection of the LazyFrame.

        Returns
        -------
        pa.Table
            PyArrow Table with same schema and data.
        """
        return self._data.collect().to_arrow()

    def to_pandas(self) -> pd.DataFrame:
        """Convert to pandas DataFrame for legacy APIs.

        Triggers collection of the LazyFrame.

        Returns
        -------
        pd.DataFrame
            pandas DataFrame with same schema and data.
        """
        return self._data.collect().to_pandas()

    @classmethod
    @abstractmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        metadata: Optional[Dict[str, Any]] = None,
        mapping: Optional[Dict[str, str]] = None,
    ) -> BaseDataset:
        """Construct dataset from pandas DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            Input data with canonical column names.
        metadata : dict, optional
            Additional metadata.
        mapping : dict[str, str], optional
            Canonical to original column mapping.

        Returns
        -------
        BaseDataset
            Constructed dataset instance.
        """
        raise NotImplementedError("Subclasses must implement from_dataframe")

    @classmethod
    @abstractmethod
    def from_arrow(
        cls,
        table: pa.Table,
        metadata: Optional[Dict[str, Any]] = None,
        mapping: Optional[Dict[str, str]] = None,
    ) -> BaseDataset:
        """Construct dataset from PyArrow Table.

        Parameters
        ----------
        table : pa.Table
            Input data with canonical column names.
        metadata : dict, optional
            Additional metadata.
        mapping : dict[str, str], optional
            Canonical to original column mapping.

        Returns
        -------
        BaseDataset
            Constructed dataset instance.
        """
        raise NotImplementedError("Subclasses must implement from_arrow")

    @classmethod
    @abstractmethod
    def from_polars(
        cls,
        df: pl.DataFrame | pl.LazyFrame,
        metadata: Optional[Dict[str, Any]] = None,
        mapping: Optional[Dict[str, str]] = None,
    ) -> BaseDataset:
        """Construct dataset from Polars DataFrame or LazyFrame.

        Parameters
        ----------
        df : pl.DataFrame | pl.LazyFrame
            Input data with canonical column names.
        metadata : dict, optional
            Additional metadata.
        mapping : dict[str, str], optional
            Canonical to original column mapping.

        Returns
        -------
        BaseDataset
            Constructed dataset instance.
        """
        raise NotImplementedError("Subclasses must implement from_polars")
