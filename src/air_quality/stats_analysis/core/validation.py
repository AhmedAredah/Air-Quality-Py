"""air_quality.stats_analysis.core.validation

Numeric column validation utilities for statistical primitives.

Constitution compliance:
- Section 3: Data validation standards (finite values, correct dtypes)
- Section 11: Vectorized validation checks (no row loops)
"""

from __future__ import annotations

import polars as pl

from ....exceptions import DataValidationError, SchemaError


def validate_numeric_column(
    data: pl.LazyFrame,
    col_name: str,
    allow_null: bool = True,
    require_finite: bool = True,
) -> None:
    """Validate that a column contains numeric data with finite values.

    Constitution References
    -----------------------
    - Section 3: Data validation (numeric types, no silent coercion)
    - Section 11: Vectorized checks (single collect for validation)

    Parameters
    ----------
    data : pl.LazyFrame
        Input dataset.
    col_name : str
        Column name to validate.
    allow_null : bool, default=True
        Whether null values are permitted.
    require_finite : bool, default=True
        Whether to enforce finite values (no inf/-inf).

    Raises
    ------
    SchemaError
        If column is missing from schema.
    DataValidationError
        If column is non-numeric, contains non-finite values (when required),
        or contains nulls (when not allowed).

    Examples
    --------
    >>> import polars as pl
    >>> data = pl.LazyFrame({'conc': [1.0, 2.0, 3.0]})
    >>> validate_numeric_column(data, 'conc')  # passes
    >>> bad_data = pl.LazyFrame({'conc': [1.0, float('inf'), 3.0]})
    >>> validate_numeric_column(bad_data, 'conc')  # raises DataValidationError
    Traceback (most recent call last):
        ...
    DataValidationError: Column 'conc' contains non-finite values...
    """
    schema = data.collect_schema()

    # Check column exists
    if col_name not in schema.names():
        raise SchemaError(
            f"Missing column '{col_name}' for validation "
            f"(Constitution Sec. 3: data schema). "
            f"Available columns: {schema.names()}"
        )

    # Check dtype is numeric
    dtype = schema[col_name]
    if not dtype.is_numeric():
        raise DataValidationError(
            f"Column '{col_name}' must be numeric (Constitution Sec. 3: data validation). "
            f"Got dtype: {dtype}"
        )

    # Collect validation checks (single pass)
    checks = data.select(
        pl.col(col_name).null_count().alias("null_count"),
        pl.col(col_name).is_infinite().sum().alias("inf_count"),
    ).collect()

    null_count = checks["null_count"][0]
    inf_count = checks["inf_count"][0]

    # Validate null constraint
    if not allow_null and null_count > 0:
        raise DataValidationError(
            f"Column '{col_name}' contains {null_count} null values, "
            f"but nulls are not allowed (Constitution Sec. 3: data validation)."
        )

    # Validate finite constraint
    if require_finite and inf_count > 0:
        raise DataValidationError(
            f"Column '{col_name}' contains {inf_count} non-finite values (inf/-inf), "
            f"but finite values are required (Constitution Sec. 3: data validation)."
        )


def validate_grouping_columns(
    data: pl.LazyFrame,
    group_by: list[str] | None,
) -> None:
    """Validate that grouping columns exist in dataset schema.

    Constitution References
    -----------------------
    - Section 3: Schema validation
    - Section 7: Module configuration validation

    Parameters
    ----------
    data : pl.LazyFrame
        Input dataset.
    group_by : list[str] | None
        Grouping column names (None is valid for global aggregation).

    Raises
    ------
    SchemaError
        If any grouping column is missing from schema.

    Examples
    --------
    >>> import polars as pl
    >>> data = pl.LazyFrame({'site_id': ['A', 'B'], 'conc': [1.0, 2.0]})
    >>> validate_grouping_columns(data, ['site_id'])  # passes
    >>> validate_grouping_columns(data, ['missing_col'])  # raises SchemaError
    Traceback (most recent call last):
        ...
    SchemaError: Grouping columns missing from schema...
    """
    if group_by is None or len(group_by) == 0:
        return  # No validation needed for global aggregation

    schema_names = data.collect_schema().names()
    missing = [col for col in group_by if col not in schema_names]

    if missing:
        raise SchemaError(
            f"Grouping columns missing from schema (Constitution Sec. 3): {missing}. "
            f"Available columns: {schema_names}"
        )
