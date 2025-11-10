"""air_quality.analysis.correlation

Pairwise correlation primitives (Pearson, Spearman) with ordered unique pairs.

Constitution compliance:
- Section 11: Vectorized correlation via pivot/covariance
- Section 15: Units presence checks (configurable override)
"""

from __future__ import annotations

from enum import Enum


class CorrelationMethod(str, Enum):
    """Correlation computation methods.

    Constitution References
    -----------------------
    - Section 7: Module configuration standards

    Methods:
    - PEARSON: Linear correlation (parametric)
    - SPEARMAN: Rank correlation (non-parametric)
    """

    PEARSON = "pearson"
    SPEARMAN = "spearman"


# Default thresholds for correlation computations
DEFAULT_MIN_SAMPLES: int = 3
"""Minimum number of valid observations for correlation analysis."""

# Correlation methods for validation
ALLOWED_CORRELATION_METHODS: frozenset[CorrelationMethod] = frozenset(
    {
        CorrelationMethod.PEARSON,
        CorrelationMethod.SPEARMAN,
    }
)
"""Allowed correlation methods."""


__all__ = [
    "CorrelationMethod",
    "DEFAULT_MIN_SAMPLES",
    "ALLOWED_CORRELATION_METHODS",
]


# Placeholder for T037, T038, T039
