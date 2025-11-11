"""air_quality.analysis.descriptive

Descriptive statistics primitives (mean, median, std, quantiles, counts).

Constitution compliance:
- Section 11: Columnar groupby/agg (Polars), no Python loops
- Section 5: QC flag filtering
"""

from .core import compute_descriptives
from .enums import DescriptiveStatsOperation, OutputFormat

__all__ = [
    "compute_descriptives",
    "DescriptiveStatsOperation",
    "OutputFormat",
]
