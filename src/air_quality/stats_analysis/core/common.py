"""air_quality.stats_analysis.core.common

Shared utilities for QC flag filtering and dataset preparation.

Constitution compliance:
- Section 3: QC flag semantics (invalid/outlier excluded, below_dl treated as missing)
- Section 11: Vectorized filtering operations (no row loops)
"""

from __future__ import annotations

from typing import Optional

import polars as pl

from ....exceptions import SchemaError
from ....qc_flags import EXCLUDE_FLAGS, MISSING_FLAGS, QCFlag


def filter_by_qc_flags(
    data: pl.LazyFrame,
    flag_col: str = "flag",
    exclude_flags: Optional[frozenset[QCFlag]] = None,
    treat_as_missing: Optional[frozenset[QCFlag]] = None,
) -> pl.LazyFrame:
    """Filter dataset by QC flags according to Constitution Sec. 3 semantics.

    Excludes rows with flags in `exclude_flags` (default: EXCLUDE_FLAGS from constants).
    Marks rows with flags in `treat_as_missing` (default: MISSING_FLAGS from constants) as missing
    by setting concentration column to null (handled by caller).

    Constitution References
    -----------------------
    - Section 3: QC flag standards (invalid/outlier excluded, below_dl as missing)
    - Section 11: Vectorized operations (filter/when expressions, no loops)

    Parameters
    ----------
    data : pl.LazyFrame
        Input dataset (canonical long schema expected).
    flag_col : str, default='flag'
        Name of the QC flag column.
    exclude_flags : frozenset[QCFlag], optional
        Flags to exclude entirely (default: {QCFlag.INVALID, QCFlag.OUTLIER}).
    treat_as_missing : frozenset[QCFlag], optional
        Flags to treat as missing (default: {QCFlag.BELOW_DL}).
        Note: This function does NOT modify concentration values;
        caller should handle missing value logic separately.

    Returns
    -------
    pl.LazyFrame
        Filtered dataset with excluded flags removed.
        Rows with treat_as_missing flags are retained but should be
        considered missing by downstream aggregations.

    Raises
    ------
    SchemaError
        If flag_col is missing from schema.

    Examples
    --------
    >>> import polars as pl
    >>> from .constants import QCFlag
    >>> data = pl.LazyFrame({
    ...     'datetime': ['2024-01-01', '2024-01-02', '2024-01-03'],
    ...     'site_id': ['A', 'A', 'A'],
    ...     'pollutant': ['PM2.5', 'PM2.5', 'PM2.5'],
    ...     'conc': [10.0, 5.0, 15.0],
    ...     'flag': ['valid', 'invalid', 'below_dl']
    ... })
    >>> filtered = filter_by_qc_flags(data)
    >>> filtered.collect()['flag'].to_list()
    ['valid', 'below_dl']
    """
    if exclude_flags is None:
        exclude_flags = EXCLUDE_FLAGS
    if treat_as_missing is None:
        treat_as_missing = MISSING_FLAGS

    # Check schema
    if flag_col not in data.collect_schema().names():
        raise SchemaError(
            f"Missing required QC flag column '{flag_col}' "
            f"(Constitution Sec. 3: QC standards). "
            f"Available columns: {data.collect_schema().names()}"
        )

    # Exclude rows with flags in exclude_flags (vectorized filter)
    if exclude_flags:
        # Convert enum values to strings for Polars comparison
        exclude_values = [flag.value for flag in exclude_flags]
        data = data.filter(~pl.col(flag_col).is_in(exclude_values))

    # Note: treat_as_missing logic handled by caller (mark conc as null)
    # This function only filters exclusions; missing value handling is context-dependent
    return data


def mark_missing_by_flags(
    data: pl.LazyFrame,
    conc_col: str = "conc",
    flag_col: str = "flag",
    missing_flags: Optional[frozenset[QCFlag]] = None,
) -> pl.LazyFrame:
    """Mark concentration values as null for rows with specified flags.

    Companion to filter_by_qc_flags for handling below_dl and similar cases.

    Constitution References
    -----------------------
    - Section 3: QC flag semantics (below_dl treated as missing)
    - Section 11: Vectorized when/otherwise expressions

    Parameters
    ----------
    data : pl.LazyFrame
        Input dataset.
    conc_col : str, default='conc'
        Concentration column name.
    flag_col : str, default='flag'
        QC flag column name.
    missing_flags : frozenset[QCFlag], optional
        Flags to mark as missing (default: {QCFlag.BELOW_DL}).

    Returns
    -------
    pl.LazyFrame
        Dataset with concentration values set to null where flag matches.

    Raises
    ------
    SchemaError
        If conc_col or flag_col missing from schema.

    Examples
    --------
    >>> import polars as pl
    >>> from .constants import QCFlag
    >>> data = pl.LazyFrame({
    ...     'conc': [10.0, 5.0, 15.0],
    ...     'flag': ['valid', 'below_dl', 'valid']
    ... })
    >>> marked = mark_missing_by_flags(data)
    >>> marked.collect()['conc'].to_list()
    [10.0, None, 15.0]
    """
    if missing_flags is None:
        missing_flags = MISSING_FLAGS

    schema_names = data.collect_schema().names()
    if conc_col not in schema_names:
        raise SchemaError(
            f"Missing concentration column '{conc_col}' "
            f"(Constitution Sec. 3: canonical schema). "
            f"Available: {schema_names}"
        )
    if flag_col not in schema_names:
        raise SchemaError(
            f"Missing QC flag column '{flag_col}' "
            f"(Constitution Sec. 3: QC standards). "
            f"Available: {schema_names}"
        )

    # Mark as null where flag in missing_flags (vectorized when/otherwise)
    if missing_flags:
        # Convert enum values to strings for Polars comparison
        missing_values = [flag.value for flag in missing_flags]
        data = data.with_columns(
            pl.when(pl.col(flag_col).is_in(missing_values))
            .then(None)
            .otherwise(pl.col(conc_col))
            .alias(conc_col)
        )

    return data
