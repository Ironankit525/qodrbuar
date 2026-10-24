from datetime import date, timedelta
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from . import analysis, config, schemas
from .data import Dataset, get_dataset

router = APIRouter(prefix="/api")

Cutoff = Annotated[
    str,
    Query(pattern=r"^([01]\d|2[0-3]):[0-5]\d$", description="Decision deadline HH:MM (UTC) on D-1"),
]
Data = Annotated[Dataset, Depends(get_dataset)]


def _records(df: pd.DataFrame) -> list[dict]:
    """DataFrame -> list of dicts with NaN converted to None."""
    return df.astype(object).where(df.notna(), None).to_dict("records")


def _decision_accuracy_frame(data: Dataset, cutoff: str) -> pd.DataFrame:
    """Decision-time forecasts joined to actuals, for every delivery hour that has an actual."""
    forecasts = analysis.decision_time_forecasts(data.forecasts, cutoff)
    return analysis.with_actuals(forecasts, data.hourly_actuals)


@router.get("/meta", response_model=schemas.Meta)
def meta():
    last_day = pd.Timestamp(config.DELIVERY_END).date() - timedelta(days=1)
    return {
        "first_delivery_date": pd.Timestamp(config.DELIVERY_START).date(),
        "last_delivery_date": last_day,
        "default_cutoff": config.DEFAULT_CUTOFF,
    }


@router.get("/forecast", response_model=schemas.DayForecast)
def day_forecast(data: Data, delivery_date: date, cutoff: Cutoff = config.DEFAULT_CUTOFF):
    """The forecast available at the cutoff for each hour of `delivery_date`."""
    forecasts = analysis.decision_time_forecasts(data.forecasts, cutoff)
    day = forecasts[forecasts["startTime"].dt.date == delivery_date]
    if day.empty:
        raise HTTPException(404, f"No forecast available for {delivery_date} at cutoff {cutoff}")

    day = day.merge(data.hourly_actuals, on="startTime", how="left")
    points = _records(day.rename(columns={
        "startTime": "start_time", "publishTime": "publish_time",
        "forecast": "forecast_mw", "actual": "actual_mw",
    }))
    return {"delivery_date": delivery_date, "cutoff": cutoff, "points": points}


@router.get("/accuracy/summary", response_model=schemas.Metrics)
def accuracy_summary(data: Data, cutoff: Cutoff = config.DEFAULT_CUTOFF):
    return analysis.error_metrics(_decision_accuracy_frame(data, cutoff))


@router.get("/accuracy/series", response_model=list[schemas.SeriesPoint])
def accuracy_series(data: Data, cutoff: Cutoff = config.DEFAULT_CUTOFF):
    frame = _decision_accuracy_frame(data, cutoff)
    return _records(frame[["startTime", "forecast", "actual"]].rename(columns={
        "startTime": "start_time", "forecast": "forecast_mw", "actual": "actual_mw",
    }))


@router.get("/accuracy/daily", response_model=list[schemas.DayMetrics])
def accuracy_daily(data: Data, cutoff: Cutoff = config.DEFAULT_CUTOFF):
    return analysis.metrics_by_day(_decision_accuracy_frame(data, cutoff))


@router.get("/accuracy/by-hour", response_model=list[schemas.HourMetrics])
def accuracy_by_hour(data: Data, cutoff: Cutoff = config.DEFAULT_CUTOFF):
    return analysis.metrics_by_hour_of_day(_decision_accuracy_frame(data, cutoff))


@router.get("/accuracy/by-horizon", response_model=list[schemas.HorizonMetrics])
def accuracy_by_horizon(data: Data):
    """Accuracy of every forecast ever published, by lead time. Independent of the cutoff."""
    forecasts = analysis.all_forecasts(data.forecasts)
    return analysis.metrics_by_horizon(analysis.with_actuals(forecasts, data.hourly_actuals))
