"""Decision-time forecast selection and forecast-accuracy metrics.

Pure functions over DataFrames; all timestamps are tz-aware UTC.
Error convention: error = forecast - actual, so a positive error means wind was over-forecast
(the trader under-bought and must cover the shortfall closer to delivery).
"""
import pandas as pd

ONE_DAY = pd.Timedelta(days=1)
ONE_HOUR = pd.Timedelta(hours=1)
HORIZON_BUCKET_HOURS = 6


def hourly_actuals(actuals: pd.DataFrame) -> pd.DataFrame:
    """Average the two half-hourly settlement periods of each hour (MW).

    WINDFOR is hourly while FUELHH is half-hourly, so actuals are aggregated to match.
    Hours missing either half-hour are dropped. Columns: startTime, actual.
    """
    by_hour = actuals.set_index("startTime")["generation"].resample("h")
    hourly = pd.DataFrame({"actual": by_hour.mean(), "periods": by_hour.count()})
    complete = hourly[hourly["periods"] == 2]
    return complete[["actual"]].reset_index()


def decision_time_forecasts(forecasts: pd.DataFrame, cutoff: str) -> pd.DataFrame:
    """The forecast a trader had at the day-ahead deadline, for every delivery hour.

    The deadline for a delivery hour is `cutoff` (HH:MM, UTC) on the previous day. We take the
    latest forecast published at or before that deadline.
    Columns: startTime, publishTime, forecast, horizon_hours.
    """
    deadline = forecasts["startTime"].dt.normalize() - ONE_DAY + pd.Timedelta(f"{cutoff}:00")
    available = forecasts[forecasts["publishTime"] <= deadline]
    latest = available.sort_values("publishTime").drop_duplicates("startTime", keep="last")
    return _with_horizon(latest.rename(columns={"generation": "forecast"})).sort_values("startTime")


def all_forecasts(forecasts: pd.DataFrame) -> pd.DataFrame:
    """Every genuine forecast (horizon >= 0). Elexon also returns back-filled past hours."""
    result = _with_horizon(forecasts.rename(columns={"generation": "forecast"}))
    return result[result["horizon_hours"] >= 0]


def with_actuals(forecasts: pd.DataFrame, hourly: pd.DataFrame) -> pd.DataFrame:
    """Join forecasts to actuals (inner) and add `error` = forecast - actual."""
    joined = forecasts.merge(hourly, on="startTime", how="inner")
    return joined.assign(error=joined["forecast"] - joined["actual"])


def error_metrics(df: pd.DataFrame) -> dict:
    """Accuracy summary (MW) for rows with `forecast`, `actual`, `error` columns."""
    abs_error = df["error"].abs()
    mean_actual = df["actual"].mean()
    mae = abs_error.mean()
    return {
        "n": len(df),
        "mean_actual_mw": mean_actual,
        "bias_mw": df["error"].mean(),
        "mae_mw": mae,
        "rmse_mw": (df["error"] ** 2).mean() ** 0.5,
        "p95_abs_error_mw": abs_error.quantile(0.95),
        "nmae_pct": mae / mean_actual * 100,
    }


def metrics_by_day(df: pd.DataFrame) -> list[dict]:
    return _grouped_metrics(df, df["startTime"].dt.strftime("%Y-%m-%d"), "date")


def metrics_by_hour_of_day(df: pd.DataFrame) -> list[dict]:
    return _grouped_metrics(df, df["startTime"].dt.hour, "hour")


def metrics_by_horizon(df: pd.DataFrame) -> list[dict]:
    """Accuracy by how far ahead the forecast was made, in 6-hour buckets."""
    bucket_start = (df["horizon_hours"] // HORIZON_BUCKET_HOURS * HORIZON_BUCKET_HOURS).astype(int)
    return _grouped_metrics(df, bucket_start, "horizon_from_h")


def _with_horizon(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(horizon_hours=(df["startTime"] - df["publishTime"]) / ONE_HOUR)


def _grouped_metrics(df: pd.DataFrame, key: pd.Series, key_name: str) -> list[dict]:
    return [{key_name: k, **error_metrics(group)} for k, group in df.groupby(key)]
