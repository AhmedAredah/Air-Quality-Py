"""air_quality.stats_analysis.core.trend

Linear trend primitives (conc ~ time) with calendar-aware time units.

Constitution compliance:
- Section 11: Closed-form OLS via sufficient statistics
- Section 15: Unit enforcement for slopes (Unit per time_unit)
- Section 3: Calendar-aware time semantics (hour/day/calendar_month/calendar_year)
"""

from __future__ import annotations

# Placeholder for T051, T052, T053
