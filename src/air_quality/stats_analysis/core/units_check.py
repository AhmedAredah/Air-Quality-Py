"""air_quality.stats_analysis.core.units_check

Unit presence validation for statistical modules.

Constitution compliance:
- Section 15: Units enforcement for trends; correlation units policy
"""

from __future__ import annotations

from typing import Optional

from ....dataset.time_series import TimeSeriesDataset
from ....exceptions import UnitError


def check_units_present(
    dataset: TimeSeriesDataset,
    pollutants: list[str],
    operation: str = "operation",
    allow_missing: bool = False,
) -> tuple[bool, list[str]]:
    """Check that units are present for specified pollutants.

    Constitution References
    -----------------------
    - Section 15: Units enforcement (required for trends, optional for correlation)

    Parameters
    ----------
    dataset : TimeSeriesDataset
        Input dataset with column_units metadata.
    pollutants : list[str]
        Pollutant identifiers to check.
    operation : str, default='operation'
        Operation name for error messages (e.g., 'trend analysis', 'correlation').
    allow_missing : bool, default=False
        If False, raises UnitError when units are missing.
        If True, returns status without raising.

    Returns
    -------
    has_units : bool
        True if all pollutants have units, False otherwise.
    missing_pollutants : list[str]
        List of pollutants with missing units.

    Raises
    ------
    UnitError
        If allow_missing=False and any pollutant lacks units.

    Examples
    --------
    >>> from air_quality.dataset.time_series import TimeSeriesDataset
    >>> from air_quality.units import Unit
    >>> import polars as pl
    >>> data = pl.LazyFrame({'datetime': ['2024-01-01'], 'site_id': ['A'],
    ...                      'pollutant': ['PM2.5'], 'conc': [10.0]})
    >>> dataset = TimeSeriesDataset(data, column_units={'PM2.5': Unit.UG_M3})
    >>> check_units_present(dataset, ['PM2.5'], 'test')
    (True, [])
    >>> dataset_no_units = TimeSeriesDataset(data)
    >>> check_units_present(dataset_no_units, ['PM2.5'], 'test', allow_missing=True)
    (False, ['PM2.5'])
    """
    column_units = dataset.column_units or {}

    # Check which pollutants are missing units
    missing_pollutants = [p for p in pollutants if p not in column_units]

    has_units = len(missing_pollutants) == 0

    if not allow_missing and not has_units:
        raise UnitError(
            f"Units required for {operation} (Constitution Sec. 15: units enforcement). "
            f"Missing units for pollutants: {missing_pollutants}. "
            f"Available units: {list(column_units.keys())}"
        )

    return has_units, missing_pollutants


def require_units_for_pollutant(
    dataset: TimeSeriesDataset,
    pollutant: str,
    operation: str = "operation",
) -> None:
    """Require that a single pollutant has unit metadata.

    Convenience wrapper for check_units_present with single pollutant.

    Constitution References
    -----------------------
    - Section 15: Units enforcement for trends

    Parameters
    ----------
    dataset : TimeSeriesDataset
        Input dataset.
    pollutant : str
        Pollutant identifier.
    operation : str, default='operation'
        Operation name for error messages.

    Raises
    ------
    UnitError
        If pollutant lacks units.

    Examples
    --------
    >>> from air_quality.dataset.time_series import TimeSeriesDataset
    >>> from air_quality.units import Unit
    >>> import polars as pl
    >>> data = pl.LazyFrame({'datetime': ['2024-01-01'], 'site_id': ['A'],
    ...                      'pollutant': ['PM2.5'], 'conc': [10.0]})
    >>> dataset = TimeSeriesDataset(data, column_units={'PM2.5': Unit.UG_M3})
    >>> require_units_for_pollutant(dataset, 'PM2.5', 'trend')  # passes
    >>> dataset_no_units = TimeSeriesDataset(data)
    >>> require_units_for_pollutant(dataset_no_units, 'PM2.5', 'trend')  # raises
    Traceback (most recent call last):
        ...
    UnitError: Units required for trend...
    """
    check_units_present(dataset, [pollutant], operation=operation, allow_missing=False)
