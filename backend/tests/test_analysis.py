import pandas as pd
import pytest

from app import analysis


def ts(s: str) -> pd.Timestamp:
    return pd.Timestamp(s, tz="UTC")


def forecast_rows(*rows) -> pd.DataFrame:
    """rows: (startTime, publishTime, generation)"""
    return pd.DataFrame(
        [(ts(s), ts(p), g) for s, p, g in rows], columns=["startTime", "publishTime", "generation"]
    )


def test_hourly_actuals_averages_half_hours_and_drops_incomplete_hours():
    actuals = pd.DataFrame({
        "startTime": [ts("2026-01-02 10:00"), ts("2026-01-02 10:30"), ts("2026-01-02 11:00")],
        "generation": [100, 200, 300],  # 11:30 missing -> 11:00 hour is incomplete
    })
    hourly = analysis.hourly_actuals(actuals)
    assert hourly["startTime"].tolist() == [ts("2026-01-02 10:00")]
    assert hourly["actual"].tolist() == [150]


def test_decision_time_uses_latest_forecast_published_before_cutoff():
    forecasts = forecast_rows(
        ("2026-01-02 10:00", "2026-01-01 09:30", 100),
        ("2026-01-02 10:00", "2026-01-01 11:30", 120),  # latest before 12:00 -> chosen
        ("2026-01-02 10:00", "2026-01-01 15:30", 999),  # after the deadline -> ignored
    )
    chosen = analysis.decision_time_forecasts(forecasts, "12:00")
    assert chosen["forecast"].tolist() == [120]
    assert chosen["publishTime"].tolist() == [ts("2026-01-01 11:30")]
    assert chosen["horizon_hours"].tolist() == [22.5]


def test_decision_time_cutoff_is_inclusive_and_changes_the_pick():
    forecasts = forecast_rows(
        ("2026-01-02 10:00", "2026-01-01 09:30", 100),
        ("2026-01-02 10:00", "2026-01-01 11:30", 120),
    )
    assert analysis.decision_time_forecasts(forecasts, "11:30")["forecast"].tolist() == [120]
    assert analysis.decision_time_forecasts(forecasts, "11:29")["forecast"].tolist() == [100]


def test_decision_time_skips_hours_with_no_eligible_forecast():
    forecasts = forecast_rows(("2026-01-02 10:00", "2026-01-01 15:30", 100))
    assert analysis.decision_time_forecasts(forecasts, "12:00").empty


def test_all_forecasts_drops_backfilled_past_hours():
    forecasts = forecast_rows(
        ("2026-01-01 21:00", "2026-01-02 22:30", 1),  # in the past at publish time
        ("2026-01-03 00:00", "2026-01-02 22:30", 2),
    )
    assert analysis.all_forecasts(forecasts)["forecast"].tolist() == [2]


def test_error_metrics():
    df = pd.DataFrame({"forecast": [110, 90, 130], "actual": [100, 100, 100]})
    df["error"] = df["forecast"] - df["actual"]  # 10, -10, 30
    m = analysis.error_metrics(df)
    assert m["n"] == 3
    assert m["bias_mw"] == pytest.approx(10)
    assert m["mae_mw"] == pytest.approx(50 / 3)
    assert m["rmse_mw"] == pytest.approx((1100 / 3) ** 0.5)
    assert m["nmae_pct"] == pytest.approx(50 / 3)
    assert m["p95_abs_error_mw"] == pytest.approx(28)


def test_metrics_by_horizon_buckets_into_six_hour_bands():
    df = pd.DataFrame({
        "startTime": [ts("2026-01-02 10:00")] * 3,
        "horizon_hours": [1.5, 5.5, 7.5],
        "forecast": [110, 120, 150],
        "actual": [100, 100, 100],
    })
    df["error"] = df["forecast"] - df["actual"]
    result = analysis.metrics_by_horizon(df)
    assert [(r["horizon_from_h"], r["n"]) for r in result] == [(0, 2), (6, 1)]
