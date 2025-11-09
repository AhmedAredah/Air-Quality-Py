# Research — Feature 002: Units & Time Primitives

Status: Phase 0 complete
Date: 2025-11-08

This document consolidates decisions, rationales, and alternatives for the Units & Time primitives. It resolves all outstanding "NEEDS CLARIFICATION" items from the spec.

## Decisions

### D1. Rounding policy granularity

- Decision: Centralized policy with per-unit defaults and optional per-pollutant overrides via a read-only registry.
- Rationale: Keeps reporting consistent while allowing pollutant-specific conventions when required by regulatory or scientific norms (Constitution Sec 8, 15).
- Alternatives considered:
  - Per-call ad-hoc rounding parameters: rejected (DRY violation, inconsistent reporting).
  - Global single precision: rejected (insufficient flexibility and contradicts pollutant-specific needs).

### D2. Dataset unit metadata validation timing

- Decision: Fail fast at dataset construction; raise UnitError and include offending column name.
- Rationale: Prevents propagation of inconsistent metadata; improves debuggability (Sec 3, 9, 15).
- Alternatives considered:
  - Lazy validation at use-time: rejected (hidden errors, harder root-cause analysis).

### D3. Resampling backend selection

- Decision: Use pandas resample inside boundary utility; keep Polars as core columnar engine elsewhere.
- Rationale: Pandas has mature, flexible resampling; boundary keeps pandas surface area minimal while preserving Polars-first architecture (Sec 11).
- Alternatives considered:
  - Pure Polars resampling: viable but less feature-complete for irregularities and offsets at this stage.
  - Dual implementations behind flag: added complexity without strong benefit now.

### D4. Time bounds precision and timezone

- Decision: Preserve sub-second precision; always return tz-aware UTC.
- Rationale: Accuracy for high-resolution sensors; consistent canonicalization (Sec 3).
- Alternatives considered:
  - Truncate to seconds: rejected (loss of information).
  - Return naive UTC: rejected (ambiguity for downstream consumers).

### D5. Initial unit scope

- Decision: Minimal concentration units only: ug/m3, mg/m3, ppm, ppb; additive extension later.
- Rationale: Keeps surface small and testable; aligns with near-term modules (Sec 15).
- Alternatives considered:
  - Include temperature/pressure: rejected (out of scope NG1; requires dimensional analysis framework).

## Best practices references (concise)

- Vectorized math for conversions; avoid Python loops (Sec 11).
- Registry pattern for rounding policy; single source of truth (Sec 7, 15).
- Immutability in utilities; pure functions for reproducibility (Sec 10, 15).
- UTC canonical time handling; explicit tz info (Sec 3).

## Resolved open questions from spec

1) Kelvin/Celsius conversions: Out of scope for 002 per NG1; to be proposed in a future feature with dimensional analysis.
2) Automatic provenance unit attachment: Deferred; this feature prepares normalized units and rounding only. Attachment to provenance occurs in module `run()` paths (Sec 15).
3) Frequency inference in resampling: Not included; require explicit rule parameter to avoid implicit behavior. May add helper later.

---
End of Phase 0 Research
