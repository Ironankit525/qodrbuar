"""Response models for the JSON API (snake_case, MW, UTC)."""
from datetime import date, datetime

from pydantic import BaseModel


class Meta(BaseModel):
    first_delivery_date: date
    last_delivery_date: date
    default_cutoff: str


class ForecastPoint(BaseModel):
    start_time: datetime
    forecast_mw: float
    publish_time: datetime
    horizon_hours: float
    actual_mw: float | None  # None while the actual is not yet available


class DayForecast(BaseModel):
    delivery_date: date
    cutoff: str
    points: list[ForecastPoint]


class SeriesPoint(BaseModel):
    start_time: datetime
    forecast_mw: float
    actual_mw: float


class Metrics(BaseModel):
    n: int
    mean_actual_mw: float
    bias_mw: float
    mae_mw: float
    rmse_mw: float
    p95_abs_error_mw: float
    nmae_pct: float


class DayMetrics(Metrics):
    date: date


class HourMetrics(Metrics):
    hour: int


class HorizonMetrics(Metrics):
    horizon_from_h: int
