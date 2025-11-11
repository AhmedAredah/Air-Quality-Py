"""Pearson correlation coefficient implementation."""

from __future__ import annotations


def compute_pearson(x: "np.ndarray", y: "np.ndarray") -> float:  # type: ignore[name-defined]  # noqa: F821
    """Compute Pearson correlation coefficient.

    Parameters
    ----------
    x : np.ndarray
        First variable values.
    y : np.ndarray
        Second variable values.

    Returns
    -------
    float
        Pearson correlation coefficient (NaN if insufficient variance).
    """
    import numpy as np

    if len(x) < 2:
        return np.nan

    # Compute means
    mean_x = np.mean(x)
    mean_y = np.mean(y)

    # Compute deviations
    dx = x - mean_x
    dy = y - mean_y

    # Compute variances
    var_x = np.sum(dx**2)
    var_y = np.sum(dy**2)

    if var_x == 0 or var_y == 0:
        # No variance (constant values)
        return np.nan

    # Compute covariance and correlation
    cov_xy = np.sum(dx * dy)
    corr = cov_xy / np.sqrt(var_x * var_y)

    return float(corr)


__all__ = ["compute_pearson"]
