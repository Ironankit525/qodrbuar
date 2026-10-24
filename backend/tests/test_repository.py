import pandas as pd

from app.repository import ACTUALS_COLS, FORECASTS_COLS, ParquetRepository


def _ts(s):
    return pd.Timestamp(s, tz="UTC")


def test_parquet_roundtrip_and_window(tmp_path):
    repo = ParquetRepository(tmp_path)
    repo.save_actuals(pd.DataFrame({
        "startTime": [_ts("2026-01-02 00:00"), _ts("2026-01-02 00:30"), _ts("2026-01-03 00:00")],
        "generation": [100, 110, 120],
    }))
    repo.save_forecasts(pd.DataFrame({
        "startTime": [_ts("2026-01-02 00:00")] * 2,
        "publishTime": [_ts("2026-01-01 09:30"), _ts("2026-01-01 11:30")],
        "generation": [90, 95],
    }))

    actuals = repo.get_actuals(_ts("2026-01-02"), _ts("2026-01-03"))
    assert list(actuals.columns) == ACTUALS_COLS
    assert actuals.generation.tolist() == [100, 110]  # end is exclusive
    assert str(actuals.startTime.dt.tz) == "UTC"

    forecasts = repo.get_forecasts(_ts("2026-01-02"), _ts("2026-01-03"))
    assert list(forecasts.columns) == FORECASTS_COLS
    assert forecasts.generation.tolist() == [90, 95]
