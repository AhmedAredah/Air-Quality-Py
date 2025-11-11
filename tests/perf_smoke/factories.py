"""Performance test factories for synthetic dataset generation.

Constitution compliance:
- Section 10: Reproducible random generation (fixed seeds)
- Section 11: Large-scale test scenarios (100k+ rows)
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import polars as pl

from air_quality.dataset.time_series import TimeSeriesDataset
from air_quality.units import Unit


def create_synthetic_timeseries(
    n_rows: int = 100_000,
    n_sites: int = 10,
    n_pollutants: int = 4,
    start_date: str = "2020-01-01",
    freq_hours: int = 1,
    seed: int = 42,
    include_flags: bool = True,
    include_uncertainty: bool = False,
    pollutant_names: Optional[list[str]] = None,
) -> TimeSeriesDataset:
    """Create synthetic time series dataset for performance testing.

    Constitution References
    -----------------------
    - Section 10: Reproducible testing (fixed seed)
    - Section 11: Performance targets (100k+ rows in <2s)

    Parameters
    ----------
    n_rows : int, default=100_000
        Total number of rows to generate.
    n_sites : int, default=10
        Number of unique sites.
    n_pollutants : int, default=4
        Number of unique pollutants.
    start_date : str, default='2020-01-01'
        Start date for time series.
    freq_hours : int, default=1
        Frequency in hours between observations.
    seed : int, default=42
        Random seed for reproducibility.
    include_flags : bool, default=True
        Whether to include QC flags.
    include_uncertainty : bool, default=False
        Whether to include uncertainty column.
    pollutant_names : list[str], optional
        Custom pollutant names (default: ['PM2.5', 'NO2', 'O3', 'CO']).

    Returns
    -------
    TimeSeriesDataset
        Synthetic dataset with canonical long schema.

    Examples
    --------
    >>> dataset = create_synthetic_timeseries(n_rows=1000, n_sites=2, n_pollutants=2)
    >>> dataset.n_rows
    1000
    >>> 'datetime' in dataset.column_names
    True
    """
    np.random.seed(seed)

    if pollutant_names is None:
        pollutant_names = ["PM2.5", "NO2", "O3", "CO"][:n_pollutants]

    # Generate datetime sequence
    start = datetime.fromisoformat(start_date)
    n_timesteps = n_rows // (n_sites * n_pollutants)
    datetimes = [start + timedelta(hours=i * freq_hours) for i in range(n_timesteps)]

    # Replicate for sites and pollutants
    data_records = []
    for site_idx in range(n_sites):
        site_id = f"SITE_{site_idx:03d}"
        for pollutant in pollutant_names:
            for dt in datetimes:
                # Generate realistic concentration values
                base_conc = {
                    "PM2.5": 15.0,
                    "NO2": 25.0,
                    "O3": 40.0,
                    "CO": 0.5,
                }.get(pollutant, 10.0)

                conc = base_conc + np.random.normal(0, base_conc * 0.3)
                conc = max(0.0, conc)  # No negative concentrations

                record = {
                    "datetime": dt,
                    "site_id": site_id,
                    "pollutant": pollutant,
                    "conc": conc,
                }

                if include_flags:
                    # 90% valid, 5% below_dl, 3% invalid, 2% outlier
                    flag_roll = np.random.random()
                    if flag_roll < 0.90:
                        flag = "valid"
                    elif flag_roll < 0.95:
                        flag = "below_dl"
                    elif flag_roll < 0.98:
                        flag = "invalid"
                    else:
                        flag = "outlier"
                    record["flag"] = flag

                if include_uncertainty:
                    record["unc"] = conc * 0.1  # 10% uncertainty

                data_records.append(record)

                if len(data_records) >= n_rows:
                    break
            if len(data_records) >= n_rows:
                break
        if len(data_records) >= n_rows:
            break

    # Create Polars DataFrame
    df = pl.DataFrame(data_records[:n_rows])

    # Define units for pollutants
    column_units = {
        "PM2.5": Unit.UG_M3,
        "NO2": Unit.PPB,
        "O3": Unit.PPB,
        "CO": Unit.PPM,
    }

    # Create TimeSeriesDataset
    dataset = TimeSeriesDataset.from_dataframe(
        df,
        column_units={p: column_units.get(p, Unit.UG_M3) for p in pollutant_names},
    )

    return dataset


def create_correlation_test_dataset(
    n_rows: int = 10_000,
    n_sites: int = 5,
    correlation_matrix: Optional[np.ndarray] = None,
    seed: int = 42,
) -> TimeSeriesDataset:
    """Create synthetic dataset with known correlation structure.

    Useful for validating correlation computation accuracy.

    Constitution References
    -----------------------
    - Section 10: Reproducible testing (fixed seed)

    Parameters
    ----------
    n_rows : int, default=10_000
        Total number of rows.
    n_sites : int, default=5
        Number of sites.
    correlation_matrix : np.ndarray, optional
        Desired correlation matrix (4x4 for 4 pollutants).
        If None, uses identity (uncorrelated).
    seed : int, default=42
        Random seed.

    Returns
    -------
    TimeSeriesDataset
        Dataset with specified correlation structure.

    Examples
    --------
    >>> import numpy as np
    >>> corr = np.array([[1.0, 0.8], [0.8, 1.0]])
    >>> dataset = create_correlation_test_dataset(n_rows=1000, correlation_matrix=corr)
    >>> dataset.n_rows
    1000
    """
    np.random.seed(seed)

    if correlation_matrix is None:
        correlation_matrix = np.eye(4)  # Uncorrelated

    n_pollutants = correlation_matrix.shape[0]
    pollutant_names = ["PM2.5", "NO2", "O3", "CO"][:n_pollutants]

    n_obs_per_site = n_rows // n_sites

    # Generate multivariate normal data with specified correlation
    mean = np.zeros(n_pollutants)
    cov = correlation_matrix * 100  # Scale for realistic values

    data_records = []
    start = datetime(2020, 1, 1)

    for site_idx in range(n_sites):
        site_id = f"SITE_{site_idx:03d}"

        # Generate correlated values
        values = np.random.multivariate_normal(mean, cov, n_obs_per_site)
        values = np.maximum(values, 0)  # No negatives

        for obs_idx in range(n_obs_per_site):
            dt = start + timedelta(hours=obs_idx)
            for pol_idx, pollutant in enumerate(pollutant_names):
                data_records.append(
                    {
                        "datetime": dt,
                        "site_id": site_id,
                        "pollutant": pollutant,
                        "conc": values[obs_idx, pol_idx],
                        "flag": "valid",
                    }
                )

    df = pl.DataFrame(data_records[:n_rows])

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
