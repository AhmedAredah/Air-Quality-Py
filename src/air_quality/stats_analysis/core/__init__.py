"""air_quality.stats_analysis.core

Core statistical primitives (vectorized, columnar operations).

All heavy computation logic lives here; modules are thin orchestrators.

Constitution Section 8 (DRY): Shared logic centralized in core.
Constitution Section 11: Polars/Arrow columnar backend, no Python row loops.
"""

__all__ = []  # Populated after primitive implementations
