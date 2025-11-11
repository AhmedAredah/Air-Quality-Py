"""Unit test utilities for stats_core tests.

Constitution compliance:
- Section 10: Reproducible testing (fixed seeds, deterministic generation)
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import polars as pl

from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.units import Unit


def create_simple_dataset(
    n_rows: int = 100,
    n_sites: int = 2,
    pollutant: str = "PM2.5",
    seed: int = 42,
    include_flags: bool = False,
) -> TimeSeriesDataset:
    """Create small synthetic dataset for unit tests.

    Constitution References
    -----------------------
    - Section 10: Reproducible testing (fixed seed)

    Parameters
    ----------
    n_rows : int, default=100
        Number of rows.
    n_sites : int, default=2
        Number of sites.
    pollutant : str, default='PM2.5'
        Pollutant name.
    seed : int, default=42
        Random seed.
    include_flags : bool, default=False
        Include QC flags column.

    Returns
    -------
    TimeSeriesDataset
        Small test dataset.

    Examples
    --------
    >>> dataset = create_simple_dataset(n_rows=50, n_sites=1)
    >>> dataset.n_rows
    50
    """
    np.random.seed(seed)

    start = datetime(2024, 1, 1)
    n_timesteps = n_rows // n_sites

    data_records = []
    for site_idx in range(n_sites):
        site_id = f"SITE_{site_idx}"
        for ts_idx in range(n_timesteps):
            dt = start + timedelta(hours=ts_idx)
            conc = 10.0 + np.random.normal(0, 2.0)
            conc = max(0.0, conc)

            record = {
                "datetime": dt,
                "site_id": site_id,
                "pollutant": pollutant,
                "conc": conc,
            }

            if include_flags:
                record["flag"] = "valid"

            data_records.append(record)

    df = pl.DataFrame(data_records[:n_rows])
    dataset = TimeSeriesDataset.from_dataframe(
        df,
        column_units={pollutant: Unit.UG_M3},
    )

    return dataset


def create_grouped_dataset(
    n_sites: int = 3,
    n_pollutants: int = 2,
    n_timesteps: int = 50,
    seed: int = 42,
) -> TimeSeriesDataset:
    """Create dataset with multiple sites and pollutants for grouping tests.

    Constitution References
    -----------------------
    - Section 10: Reproducible testing

    Parameters
    ----------
    n_sites : int, default=3
        Number of sites.
    n_pollutants : int, default=2
        Number of pollutants.
    n_timesteps : int, default=50
        Number of timesteps per site/pollutant.
    seed : int, default=42
        Random seed.

    Returns
    -------
    TimeSeriesDataset
        Multi-group test dataset.

    Examples
    --------
    >>> dataset = create_grouped_dataset(n_sites=2, n_pollutants=2, n_timesteps=10)
    >>> dataset.n_rows
    40
    """
    np.random.seed(seed)

    pollutant_names = ["PM2.5", "NO2", "O3", "CO"][:n_pollutants]
    start = datetime(2024, 1, 1)

    data_records = []
    for site_idx in range(n_sites):
        site_id = f"SITE_{site_idx}"
        for pollutant in pollutant_names:
            base = {"PM2.5": 15.0, "NO2": 25.0, "O3": 40.0, "CO": 0.5}.get(
                pollutant, 10.0
            )
            for ts_idx in range(n_timesteps):
                dt = start + timedelta(hours=ts_idx)
                conc = base + np.random.normal(0, base * 0.2)
                conc = max(0.0, conc)

                data_records.append(
                    {
                        "datetime": dt,
                        "site_id": site_id,
                        "pollutant": pollutant,
                        "conc": conc,
                        "flag": "valid",
                    }
                )

    df = pl.DataFrame(data_records)

    column_units = {
        "PM2.5": Unit.UG_M3,
        "NO2": Unit.PPB,
        "O3": Unit.PPB,
        "CO": Unit.PPM,
    }

    dataset = TimeSeriesDataset.from_dataframe(
        df,
        column_units={p: column_units.get(p, Unit.UG_M3) for p in pollutant_names},
    )

    return dataset


def create_flagged_dataset(
    n_rows: int = 100,
    valid_fraction: float = 0.8,
    below_dl_fraction: float = 0.1,
    invalid_fraction: float = 0.05,
    outlier_fraction: float = 0.05,
    seed: int = 42,
) -> TimeSeriesDataset:
    """Create dataset with specific flag distribution for QC tests.

    Constitution References
    -----------------------
    - Section 3: QC flag semantics
    - Section 10: Reproducible testing

    Parameters
    ----------
    n_rows : int, default=100
        Number of rows.
    valid_fraction : float, default=0.8
        Fraction of valid observations.
    below_dl_fraction : float, default=0.1
        Fraction below detection limit.
    invalid_fraction : float, default=0.05
        Fraction invalid.
    outlier_fraction : float, default=0.05
        Fraction outliers.
    seed : int, default=42
        Random seed.

    Returns
    -------
    TimeSeriesDataset
        Dataset with specified flag distribution.

    Examples
    --------
    >>> dataset = create_flagged_dataset(n_rows=100, valid_fraction=0.9)
    >>> flags = dataset.data.collect()['flag']
    >>> (flags == 'valid').sum() / len(flags) >= 0.85
    True
    """
    np.random.seed(seed)

    start = datetime(2024, 1, 1)

    # Generate flag distribution
    flags = []
    fractions = [valid_fraction, below_dl_fraction, invalid_fraction, outlier_fraction]
    flag_types = ["valid", "below_dl", "invalid", "outlier"]

    for frac, flag_type in zip(fractions, flag_types):
        n = int(n_rows * frac)
        flags.extend([flag_type] * n)

    # Fill remaining with valid
    while len(flags) < n_rows:
        flags.append("valid")

    # Shuffle
    np.random.shuffle(flags)
    flags = flags[:n_rows]

    data_records = []
    for idx in range(n_rows):
        dt = start + timedelta(hours=idx)
        conc = 10.0 + np.random.normal(0, 2.0)
        conc = max(0.0, conc)

        data_records.append(
            {
                "datetime": dt,
                "site_id": "SITE_A",
                "pollutant": "PM2.5",
                "conc": conc,
                "flag": flags[idx],
            }
        )

    df = pl.DataFrame(data_records)
    dataset = TimeSeriesDataset.from_dataframe(
        df,
        column_units={"PM2.5": Unit.UG_M3},
    )

    return dataset


def create_linear_trend_dataset(
    slope: float = 0.5,
    intercept: float = 10.0,
    n_days: int = 365,
    noise_std: float = 1.0,
    seed: int = 42,
) -> TimeSeriesDataset:
    """Create dataset with known linear trend for trend analysis tests.

    Constitution References
    -----------------------
    - Section 10: Reproducible testing (known ground truth)

    Parameters
    ----------
    slope : float, default=0.5
        Slope of trend (concentration units per day).
    intercept : float, default=10.0
        Intercept at day 0.
    n_days : int, default=365
        Number of days.
    noise_std : float, default=1.0
        Standard deviation of Gaussian noise.
    seed : int, default=42
        Random seed.

    Returns
    -------
    TimeSeriesDataset
        Dataset with linear trend + noise.

    Examples
    --------
    >>> dataset = create_linear_trend_dataset(slope=1.0, n_days=100)
    >>> dataset.n_rows
    100
    """
    np.random.seed(seed)

    start = datetime(2024, 1, 1)

    data_records = []
    for day_idx in range(n_days):
        dt = start + timedelta(days=day_idx)
        conc = intercept + slope * day_idx + np.random.normal(0, noise_std)
        conc = max(0.0, conc)

        data_records.append(
            {
                "datetime": dt,
                "site_id": "SITE_A",
                "pollutant": "PM2.5",
                "conc": conc,
                "flag": "valid",
            }
        )

    df = pl.DataFrame(data_records)
    dataset = TimeSeriesDataset.from_dataframe(
        df,
        column_units={"PM2.5": Unit.UG_M3},
    )

    return dataset
