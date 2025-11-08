"""air_quality.provenance

Provenance record structures and helpers for module runs.

Responsibilities:
- Provide a serializable `ProvenanceRecord` capturing module/domain identity,
  dataset identifier (if available), a stable configuration hash, run timestamp
  (UTC ISO 8601), and library version.
- Offer `make_provenance(module, dataset, config)` to construct the record.

Hashing strategy:
- Deterministically JSON-serialize the `config` using sorted keys and compact
  separators, then compute a SHA256 hex digest. Non-serializable objects raise
  `TypeError` (surfaced to caller) to enforce configuration purity.

Timestamp:
- Generated in UTC using `datetime.datetime.now(datetime.timezone.utc)` and
  formatted via `.isoformat()` (e.g., 2025-11-08T12:34:56.123456+00:00).
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
import datetime as _dt
from typing import Any, Dict, Mapping

from . import __version__ as _AQ_VERSION


@dataclass(slots=True)
class ProvenanceRecord:
    module_name: str
    domain: str
    dataset_id: str | None
    config_hash: str
    run_timestamp: str
    software_version: str
    extra: Dict[str, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:  # explicit for clarity / future control
        d = asdict(self)
        # Maintain key ordering for readability (Python 3.7+ preserves insertion order)
        return d


def _stable_config_hash(config: Mapping[str, Any] | Dict[str, Any]) -> str:
    try:
        serialized = json.dumps(config, sort_keys=True, separators=(",", ":"))
    except TypeError as e:  # Non-serializable entry
        raise TypeError(
            "Configuration must be JSON-serializable for provenance hashing"
        ) from e
    return sha256(serialized.encode("utf-8")).hexdigest()


def make_provenance(
    *,
    module_name: str,
    domain: str,
    dataset_id: str | None,
    config: Mapping[str, Any] | Dict[str, Any],
    extra: Dict[str, Any] | None = None,
) -> ProvenanceRecord:
    """Construct a provenance record.

    Parameters
    ----------
    module_name: str
        Name of the analysis module producing outputs.
    domain: str
        Domain or thematic grouping.
    dataset_id: str | None
        Stable identifier for the dataset if available.
    config: Mapping[str, Any]
        Configuration dict used for the run (JSON-serializable).
    extra: dict | None
        Optional additional audit metadata.
    """

    ts = _dt.datetime.now(_dt.timezone.utc).isoformat()
    cfg_hash = _stable_config_hash(config)
    return ProvenanceRecord(
        module_name=module_name,
        domain=domain,
        dataset_id=dataset_id,
        config_hash=cfg_hash,
        run_timestamp=ts,
        software_version=_AQ_VERSION,
        extra=extra or None,
    )
