"""Loads the delivery-window data once and keeps it in memory (it is small and read-only)."""
from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from . import analysis, config
from .repository import ParquetRepository


@dataclass(frozen=True)
class Dataset:
    forecasts: pd.DataFrame  # raw WINDFOR rows for the delivery window
    hourly_actuals: pd.DataFrame


@lru_cache
def get_dataset() -> Dataset:
    repo = ParquetRepository(config.DATA_DIR)
    start, end = pd.Timestamp(config.DELIVERY_START), pd.Timestamp(config.DELIVERY_END)
    return Dataset(
        forecasts=repo.get_forecasts(start, end),
        hourly_actuals=analysis.hourly_actuals(repo.get_actuals(start, end)),
    )
