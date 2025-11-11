"""Enumerations for descriptive statistics.

Constitution compliance:
- Section 7: Module output standards
"""

from enum import Enum


class OutputFormat(str, Enum):
    """Output format for descriptive statistics.

    Constitution References
    -----------------------
    - Section 7: Module output standards

    Formats:
    - TIDY: Long format with 'stat' column (one row per statistic per group)
    - WIDE: Wide format with separate columns for each statistic
    """

    TIDY = "tidy"
    WIDE = "wide"


class DescriptiveStatsOperation(Enum):
    """Individual statistic operations available in DescriptiveStatsModule.

    Attributes
    ----------
    MEAN : str
        Compute mean/average.
    MEDIAN : str
        Compute median (50th percentile).
    STD : str
        Compute standard deviation.
    MIN : str
        Compute minimum value.
    MAX : str
        Compute maximum value.
    COUNT : str
        Compute count of valid observations.
    QUANTILES : str
        Compute quantiles (configurable percentiles).
    """

    MEAN = "mean"
    MEDIAN = "median"
    STD = "std"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    QUANTILES = "quantiles"


__all__ = ["OutputFormat", "DescriptiveStatsOperation"]
