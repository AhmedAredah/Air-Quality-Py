"""air_quality.stats_analysis.core.provenance_helpers

Provenance attachment utilities for statistical analysis results.

Constitution compliance:
- Section 15: Provenance requirements (config hash, methods, thresholds, time bounds)
- Section 10: Reproducibility (deterministic config hashing)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any, Dict, Optional

import polars as pl

from ....time_utils import TimeBounds, compute_time_bounds


def compute_config_hash(config: Any) -> str:
    """Compute deterministic hash of configuration object.

    Constitution References
    -----------------------
    - Section 10: Reproducibility (stable config hashing)
    - Section 15: Provenance (config hash attachment)

    Parameters
    ----------
    config : Any
        Configuration object (dataclass, dict, or JSON-serializable).

    Returns
    -------
    str
        SHA256 hex digest of config JSON representation.

    Examples
    --------
    >>> from dataclasses import dataclass
    >>> @dataclass
    ... class Config:
    ...     method: str = "pearson"
    ...     min_samples: int = 3
    >>> config = Config()
    >>> hash1 = compute_config_hash(config)
    >>> hash2 = compute_config_hash(config)
    >>> hash1 == hash2
    True
    """
    # Convert dataclass to dict
    if is_dataclass(config):
        config_dict = asdict(config)
    elif isinstance(config, dict):
        config_dict = config
    else:
        raise TypeError(f"Config must be dataclass or dict, got {type(config)}")

    # Serialize to JSON with sorted keys for determinism
    config_json = json.dumps(config_dict, sort_keys=True, default=str)

    # Compute SHA256 hash
    return hashlib.sha256(config_json.encode()).hexdigest()


def attach_provenance(
    results: pl.DataFrame,
    module_name: str,
    domain: str,
    config: Any,
    methods: Optional[Dict[str, str]] = None,
    thresholds: Optional[Dict[str, Any]] = None,
    time_bounds: Optional[TimeBounds] = None,
    units_status: Optional[Dict[str, Any]] = None,
) -> pl.DataFrame:
    """Attach provenance metadata columns to results DataFrame.

    Constitution References
    -----------------------
    - Section 15: Provenance attachment (config hash, methods, thresholds, time bounds)
    - Section 8: Dashboard reporting (provenance fields in payload)

    Parameters
    ----------
    results : pl.DataFrame
        Statistical results (tidy format).
    module_name : str
        Module identifier (e.g., 'DescriptiveStatsModule').
    domain : str
        Analysis domain (e.g., 'descriptive_stats', 'correlation', 'trend').
    config : Any
        Configuration object (will be hashed).
    methods : dict[str, str], optional
        Methods used (e.g., {'correlation': 'pearson'}).
    thresholds : dict[str, Any], optional
        Threshold values (e.g., {'min_samples': 3, 'min_duration_years': 1.0}).
    time_bounds : TimeBounds, optional
        Time bounds of input data.
    units_status : dict[str, Any], optional
        Units enforcement status (e.g., {'missing_units': [], 'override': False}).

    Returns
    -------
    pl.DataFrame
        Results with provenance columns added.

    Examples
    --------
    >>> import polars as pl
    >>> from dataclasses import dataclass
    >>> @dataclass
    ... class Config:
    ...     method: str = "pearson"
    >>> results = pl.DataFrame({'stat': ['mean'], 'value': [10.0]})
    >>> prov = attach_provenance(
    ...     results, 'DescriptiveStatsModule', 'descriptive_stats', Config()
    ... )
    >>> 'config_hash' in prov.columns
    True
    """
    config_hash = compute_config_hash(config)

    # Build provenance dict
    prov_dict: Dict[str, Any] = {
        "module_name": module_name,
        "domain": domain,
        "config_hash": config_hash,
    }

    if methods:
        prov_dict["methods"] = json.dumps(methods, sort_keys=True)

    if thresholds:
        prov_dict["thresholds"] = json.dumps(thresholds, sort_keys=True)

    if time_bounds:
        prov_dict["time_bounds_start"] = time_bounds.start.isoformat()
        prov_dict["time_bounds_end"] = time_bounds.end.isoformat()

    if units_status:
        prov_dict["units_status"] = json.dumps(units_status, sort_keys=True)

    # Add provenance columns to results
    for key, value in prov_dict.items():
        results = results.with_columns(pl.lit(value).alias(key))

    return results


def build_provenance_from_dataset(
    dataset: Any,  # TimeSeriesDataset
    config: Any,
    module_name: str,
    domain: str,
    methods: Optional[Dict[str, str]] = None,
    thresholds: Optional[Dict[str, Any]] = None,
    units_status: Optional[Dict[str, Any]] = None,
    time_col: str = "datetime",
) -> Dict[str, Any]:
    """Build complete provenance record from dataset and configuration.

    Integrates time bounds computation (Constitution Sec. 11: single collect).

    Constitution References
    -----------------------
    - Section 15: Provenance (config hash, methods, thresholds, time bounds)
    - Section 11: Performance (single collect for time bounds)

    Parameters
    ----------
    dataset : TimeSeriesDataset
        Input dataset (with LazyFrame data attribute).
    config : Any
        Configuration object.
    module_name : str
        Module identifier.
    domain : str
        Analysis domain.
    methods : dict[str, str], optional
        Methods used.
    thresholds : dict[str, Any], optional
        Threshold values.
    units_status : dict[str, Any], optional
        Units enforcement status.
    time_col : str, default='datetime'
        Time column name for bounds computation.

    Returns
    -------
    dict[str, Any]
        Complete provenance record.

    Examples
    --------
    >>> import polars as pl
    >>> from air_quality.dataset.time_series import TimeSeriesDataset
    >>> from dataclasses import dataclass
    >>> @dataclass
    ... class Config:
    ...     method: str = "pearson"
    >>> data = pl.LazyFrame({
    ...     'datetime': ['2024-01-01', '2024-01-02'],
    ...     'site_id': ['A', 'A'],
    ...     'pollutant': ['PM2.5', 'PM2.5'],
    ...     'conc': [10.0, 15.0]
    ... })
    >>> dataset = TimeSeriesDataset.from_dataframe(data.collect())
    >>> prov = build_provenance_from_dataset(
    ...     dataset, Config(), 'TestModule', 'test'
    ... )
    >>> 'config_hash' in prov
    True
    """
    config_hash = compute_config_hash(config)

    # Compute time bounds from dataset (single collect)
    time_bounds = compute_time_bounds(dataset.data, time_col=time_col)

    # Build provenance record
    prov_record: Dict[str, Any] = {
        "module_name": module_name,
        "domain": domain,
        "config_hash": config_hash,
        "time_bounds_start": time_bounds.start.isoformat(),
        "time_bounds_end": time_bounds.end.isoformat(),
    }

    if methods:
        prov_record["methods"] = methods

    if thresholds:
        prov_record["thresholds"] = thresholds

    if units_status:
        prov_record["units_status"] = units_status

    return prov_record
