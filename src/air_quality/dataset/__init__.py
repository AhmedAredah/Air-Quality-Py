"""air_quality.dataset

Dataset abstractions with Polars LazyFrame backend.
"""

from .base import BaseDataset
from .time_series import TimeSeriesDataset

__all__ = ["BaseDataset", "TimeSeriesDataset"]
