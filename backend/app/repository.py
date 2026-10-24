"""Parquet-backed storage for wind actuals and forecasts (all timestamps tz-aware UTC).

  actuals.parquet:   startTime, generation
  forecasts.parquet: startTime, publishTime, generation
"""
from datetime import datetime
from pathlib import Path

import pandas as pd

ACTUALS_COLS = ["startTime", "generation"]
FORECASTS_COLS = ["startTime", "publishTime", "generation"]


class ParquetRepository:
    def __init__(self, data_dir: Path):
        self.dir = Path(data_dir)

    def get_actuals(self, start: datetime, end: datetime) -> pd.DataFrame:
        return self._read("actuals", ACTUALS_COLS, start, end)

    def get_forecasts(self, start: datetime, end: datetime) -> pd.DataFrame:
        return self._read("forecasts", FORECASTS_COLS, start, end)

    def save_actuals(self, df: pd.DataFrame) -> None:
        self._write("actuals", df)

    def save_forecasts(self, df: pd.DataFrame) -> None:
        self._write("forecasts", df)

    def _read(self, name: str, cols: list[str], start: datetime, end: datetime) -> pd.DataFrame:
        path = self.dir / f"{name}.parquet"
        if not path.exists():
            raise FileNotFoundError(f"{path} not found - run `python -m scripts.ingest` first")
        df = pd.read_parquet(path)[cols]
        in_window = (df["startTime"] >= pd.Timestamp(start)) & (df["startTime"] < pd.Timestamp(end))
        return df[in_window].sort_values(cols[:-1]).reset_index(drop=True)

    def _write(self, name: str, df: pd.DataFrame) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        df.to_parquet(self.dir / f"{name}.parquet", index=False)
