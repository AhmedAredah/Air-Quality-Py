"""air_quality.qc_flags

Quality control flag definitions and semantics for air quality data.

Constitution compliance:
- Section 3: QC flag standards (invalid/outlier excluded, below_dl as missing)
- Section 5: Quality control validation requirements

This module provides:
- QCFlag Enum: Controlled vocabulary for data quality flags
- Flag sets: Pre-defined groups for filtering and validation
- Semantic documentation: Clear interpretation of each flag
"""

from __future__ import annotations

from enum import Enum


class QCFlag(str, Enum):
    """Quality control flag values for air quality data.

    Constitution References
    -----------------------
    - Section 3: QC flag semantics and filtering rules
    - Section 5: Quality control validation standards

    Flag Semantics
    --------------
    VALID : str
        Clean observation passing all QC checks.
        Included in all statistical computations.

    BELOW_DL : str
        Measurement below detection limit.
        **Treated as missing** in statistical computations (excluded from mean/median
        but counted in n_total). Not excluded from dataset.

    INVALID : str
        Invalid observation (instrument malfunction, calibration error, etc.).
        **Excluded entirely** from statistical computations and counts.

    OUTLIER : str
        Statistical outlier flagged by QC algorithms.
        **Excluded entirely** from statistical computations and counts.

    Usage Guidelines
    ----------------
    - **Exclusion**: Remove INVALID and OUTLIER rows before analysis
    - **Missing treatment**: Mark BELOW_DL as null in concentration columns
    - **Provenance**: Always report n_total, n_valid, n_missing in results

    Examples
    --------
    >>> QCFlag.VALID.value
    'valid'
    >>> QCFlag.BELOW_DL in MISSING_FLAGS
    True
    >>> QCFlag.INVALID in EXCLUDE_FLAGS
    True
    """

    VALID = "valid"
    BELOW_DL = "below_dl"
    INVALID = "invalid"
    OUTLIER = "outlier"


# Pre-defined flag sets for filtering (Constitution Sec. 3)
EXCLUDE_FLAGS: frozenset[QCFlag] = frozenset({QCFlag.INVALID, QCFlag.OUTLIER})
"""QC flags to exclude entirely from statistical computations.

Rows with these flags are removed before analysis and not counted in n_total.
Constitution Section 3: Invalid and outlier data excluded from all metrics.
"""

MISSING_FLAGS: frozenset[QCFlag] = frozenset({QCFlag.BELOW_DL})
"""QC flags treated as missing values in statistical computations.

Rows with these flags are included in n_total but excluded from mean/median/etc.
Concentration values are marked as null before aggregation.
Constitution Section 3: Below detection limit treated as censored data.
"""


# Import here to avoid circular dependency
from typing import Optional

import polars as pl

from .exceptions import SchemaError


def filter_by_qc_flags(
    data: pl.LazyFrame,
    flag_col: str = "flag",
    exclude_flags: Optional[frozenset[QCFlag]] = None,
    treat_as_missing: Optional[frozenset[QCFlag]] = None,
) -> pl.LazyFrame:
    """Filter dataset by QC flags according to Constitution Sec. 3 semantics.

    Excludes rows with flags in `exclude_flags` (default: EXCLUDE_FLAGS).
    Marks rows with flags in `treat_as_missing` (default: MISSING_FLAGS) as missing
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


__all__ = [
    "QCFlag",
    "EXCLUDE_FLAGS",
    "MISSING_FLAGS",
    "filter_by_qc_flags",
    "mark_missing_by_flags",
]
