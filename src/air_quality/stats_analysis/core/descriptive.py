"""air_quality.stats_analysis.core.descriptive

Descriptive statistics primitives (mean, median, std, quantiles, counts).

Constitution compliance:
- Section 11: Columnar groupby/agg (Polars), no Python loops
- Section 5: QC flag filtering (exclude invalid/outlier, treat below_dl as missing)
"""

from __future__ import annotations

# Placeholder for T010, T023, T024
