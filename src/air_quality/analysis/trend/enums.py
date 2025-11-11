"""Enumerations for trend analysis."""

from enum import Enum


class TrendOperation(str, Enum):
    """Trend analysis operations available.

    Attributes
    ----------
    LINEAR_TREND : str
        Compute linear trend using OLS regression (slope, intercept, R²).
    """

    LINEAR_TREND = "linear_trend"


__all__ = ["TrendOperation"]
