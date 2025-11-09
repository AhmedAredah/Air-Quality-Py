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


__all__ = [
    "QCFlag",
    "EXCLUDE_FLAGS",
    "MISSING_FLAGS",
]
