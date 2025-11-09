"""air_quality.exceptions

Exception taxonomy for the air_quality library. Centralizes common error
types to enforce consistent failure modes across modules and utilities.

Usage guidelines:
- SchemaError: Column/schema mapping issues (missing/ambiguous fields)
- DataValidationError: Invalid dataset content or empty inputs
- InputValidationError: Invalid input types or argument values
- UnitError: Unit parsing/compatibility problems (reserved for future)
- TimeError: Time/datetime operations failures
- AlgorithmConvergenceError: Iterative algorithms failed to converge
- ConfigurationError: Invalid/unsupported config values
- PerformanceWarning: Non-fatal performance concerns (e.g., fallback path)
"""

from __future__ import annotations


class SchemaError(Exception):
    """Raised when canonical schema requirements are not satisfied.

    Typical triggers: missing required columns, ambiguous synonym matches,
    or incompatible types during canonicalization.
    """


class DataValidationError(Exception):
    """Raised when dataset-level validation fails.

    Examples: empty dataset after filtering, invalid value ranges, or
    inconsistent indexing for time series.
    """


class InputValidationError(Exception):
    """Raised when input arguments have invalid types or values.

    Examples: unsupported DataFrame types, invalid parameter types,
    or arguments that fail precondition checks.
    """


class UnitError(Exception):
    """Raised when unit conversion or compatibility fails.

    Placeholder for future unit registry integration.
    """


class TimeError(Exception):
    """Raised when time/datetime operations fail.

    Examples: invalid datetime types, timezone conversion issues,
    missing datetime columns in time bounds computation.
    """


class AlgorithmConvergenceError(Exception):
    """Raised when an algorithm fails to converge within constraints."""


class ConfigurationError(Exception):
    """Raised for invalid or unsupported configuration values."""


class PerformanceWarning(Warning):
    """Warning for non-fatal performance issues.

    Use to signal fallback implementations, suboptimal paths, or potential
    memory/copy concerns that do not invalidate results.
    """
