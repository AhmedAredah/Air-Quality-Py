"""air_quality.provenance

Provenance record structures and helpers for module runs.

Responsibilities:
- Provide a serializable `ProvenanceRecord` capturing module/domain identity,
  dataset identifier (if available), a stable configuration hash, run timestamp
  (UTC ISO 8601), and library version.
- Offer `make_provenance(module, dataset, config)` to construct the record.

Storage and serialization:
- `module` and `domain` are stored as Enum instances internally for type safety.
- The `to_dict()` method converts Enum instances to their string values for
  JSON serialization.
- Extra metadata keys (if present) are also converted from Enum to string values
  during serialization.

Hashing strategy:
- Accepts config with Enum keys and converts them to string values before hashing.
- All keys (config, extra) must be Enum types for type safety.
- Deterministically JSON-serialize the `config` using sorted keys and compact
  separators, then compute a SHA256 hex digest. Non-serializable objects raise
  `TypeError` (surfaced to caller) to enforce configuration purity.

Timestamp:
- Generated in UTC using `datetime.datetime.now(datetime.timezone.utc)` and
  formatted via `.isoformat()` (e.g., 2025-11-08T12:34:56.123456+00:00).
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from hashlib import sha256
import json
import datetime as _dt
from typing import Any, Dict, Mapping

from . import __version__ as _AQ_VERSION


@dataclass(slots=True)
class ProvenanceRecord:
    module: Enum
    domain: Enum
    dataset_id: str | None
    config_hash: str
    run_timestamp: str
    software_version: str
    extra: Dict[Enum, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:  # explicit for clarity / future control
        d = asdict(self)
        # Convert Enum fields to their string values for serialization
        if isinstance(d.get("module"), Enum):
            d["module"] = d["module"].value
        if isinstance(d.get("domain"), Enum):
            d["domain"] = d["domain"].value
        # Convert extra dict Enum keys to string values if present
        if d.get("extra"):
            d["extra"] = {
                (k.value if isinstance(k, Enum) else k): v
                for k, v in d["extra"].items()
            }
        # Maintain key ordering for readability (Python 3.7+ preserves insertion order)
        return d


def _stable_config_hash(config: Mapping[Enum, Any] | Dict[Enum, Any]) -> str:
    """Compute stable hash of configuration dict.

    Converts Enum keys to their string values before hashing to ensure
    deterministic serialization.

    Parameters
    ----------
    config : Mapping[Enum, Any] | Dict[Enum, Any]
        Configuration dictionary with Enum keys.

    Returns
    -------
    str
        SHA256 hex digest of the serialized configuration.

    Raises
    ------
    TypeError
        If configuration contains non-JSON-serializable values.
    """
    # Convert Enum keys to their string values
    serializable_config = {k.value: v for k, v in config.items()}

    try:
        serialized = json.dumps(
            serializable_config, sort_keys=True, separators=(",", ":")
        )
    except TypeError as e:  # Non-serializable entry
        raise TypeError(
            "Configuration must be JSON-serializable for provenance hashing"
        ) from e
    return sha256(serialized.encode("utf-8")).hexdigest()


def make_provenance(
    *,
    module: Enum,
    domain: Enum,
    dataset_id: str | None,
    config: Mapping[Enum, Any] | Dict[Enum, Any],
    extra: Dict[Enum, Any] | None = None,
) -> ProvenanceRecord:
    """Construct a provenance record.

    Parameters
    ----------
    module: Enum
        Module identifier (Enum type) for the analysis producing outputs.
        Stored as Enum, serialized to string value via to_dict().
    domain: Enum
        Domain or thematic grouping (Enum type).
        Stored as Enum, serialized to string value via to_dict().
    dataset_id: str | None
        Stable identifier for the dataset if available.
    config: Mapping[Enum, Any] | Dict[Enum, Any]
        Configuration dict with Enum keys (JSON-serializable values).
        Enum keys will be converted to their string values for hashing.
    extra: Dict[Enum, Any] | None
        Optional additional audit metadata with Enum keys.
        Enum keys will be converted to string values during serialization.
    """

    ts = _dt.datetime.now(_dt.timezone.utc).isoformat()
    cfg_hash = _stable_config_hash(config)

    return ProvenanceRecord(
        module=module,
        domain=domain,
        dataset_id=dataset_id,
        config_hash=cfg_hash,
        run_timestamp=ts,
        software_version=_AQ_VERSION,
        extra=extra or None,
    )
