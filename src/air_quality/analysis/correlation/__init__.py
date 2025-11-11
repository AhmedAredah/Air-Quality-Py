"""air_quality.analysis.correlation

Pairwise correlation primitives (Pearson, Spearman) with ordered unique pairs.

Constitution compliance:
- Section 11: Vectorized correlation via pivot/covariance
- Section 15: Units presence checks (configurable override)
"""

from .constants import DEFAULT_MIN_SAMPLES
from .core import compute_pairwise
from .enums import CorrelationOperation, OutputFormat

__all__ = [
    "compute_pairwise",
    "CorrelationOperation",
    "OutputFormat",
    "DEFAULT_MIN_SAMPLES",
]
