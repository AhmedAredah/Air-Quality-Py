"""Enumerations for correlation analysis.

Constitution compliance:
- Section 7: Module output standards
"""

from enum import Enum


class CorrelationOperation(str, Enum):
    """Correlation methods available in CorrelationModule.

    Attributes
    ----------
    PEARSON : str
        Compute Pearson correlation (linear relationships).
    SPEARMAN : str
        Compute Spearman correlation (monotonic relationships).
    """

    PEARSON = "pearson"
    SPEARMAN = "spearman"


class OutputFormat(str, Enum):
    """Output format for correlation results.

    Constitution References
    -----------------------
    - Section 7: Module output standards

    Formats:
    - TIDY: Long format with var_x, var_y columns (one row per pair per group)
    - WIDE: Wide format correlation matrix (var_x as rows, var_y as columns)
    """

    TIDY = "tidy"
    WIDE = "wide"


__all__ = ["CorrelationOperation", "OutputFormat"]
