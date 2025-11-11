"""Spearman rank correlation implementation."""

from __future__ import annotations

from .pearson import compute_pearson


def compute_spearman(x: "np.ndarray", y: "np.ndarray") -> float:  # type: ignore[name-defined]  # noqa: F821
    """Compute Spearman rank correlation coefficient.

    Parameters
    ----------
    x : np.ndarray
        First variable values.
    y : np.ndarray
        Second variable values.

    Returns
    -------
    float
        Spearman correlation coefficient (NaN if insufficient variance).
    """
    import numpy as np
    from scipy.stats import rankdata

    if len(x) < 2:
        return np.nan

    # Compute ranks (handle ties with average method)
    rank_x = rankdata(x, method="average")
    rank_y = rankdata(y, method="average")

    # Compute Pearson on ranks
    return compute_pearson(rank_x, rank_y)


__all__ = ["compute_spearman"]
