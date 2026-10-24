"""Fetch January 2026 wind actuals and forecasts from Elexon and store them.

Usage (from backend/):  python -m scripts.ingest
Writes Parquet files to DATA_DIR.
"""
from app import config
from app.elexon_client import fetch_actuals, fetch_forecasts
from app.repository import ParquetRepository


def main() -> None:
    repo = ParquetRepository(config.DATA_DIR)

    actuals = fetch_actuals(config.ACTUALS_PUBLISH_FROM, config.ACTUALS_PUBLISH_TO)
    print(f"Actuals:   {len(actuals):>6} rows  {actuals.startTime.min()} -> {actuals.startTime.max()}")
    repo.save_actuals(actuals)

    forecasts = fetch_forecasts(config.FORECASTS_PUBLISH_FROM, config.FORECASTS_PUBLISH_TO)
    print(f"Forecasts: {len(forecasts):>6} rows  {forecasts.publishTime.nunique()} publishes")
    repo.save_forecasts(forecasts)


if __name__ == "__main__":
    main()
