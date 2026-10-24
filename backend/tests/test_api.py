from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_meta():
    body = client.get("/api/meta").json()
    assert body["first_delivery_date"] == "2026-01-02"
    assert body["last_delivery_date"] == "2026-02-01"
    assert body["default_cutoff"] == "09:20"


def test_day_forecast_only_uses_forecasts_published_before_the_default_cutoff():
    body = client.get("/api/forecast", params={"delivery_date": "2026-01-15"}).json()
    assert body["cutoff"] == "09:20"
    assert len(body["points"]) == 24
    assert all(p["publish_time"] <= "2026-01-14T09:20:00Z" for p in body["points"])
    assert all(p["actual_mw"] is not None for p in body["points"])


def test_day_forecast_outside_window_is_404():
    assert client.get("/api/forecast", params={"delivery_date": "2026-03-01"}).status_code == 404


def test_invalid_cutoff_is_rejected():
    assert client.get("/api/accuracy/summary", params={"cutoff": "25:99"}).status_code == 422


def test_accuracy_endpoints_cover_whole_month():
    assert client.get("/api/accuracy/summary").json()["n"] == 744
    assert len(client.get("/api/accuracy/daily").json()) == 31
    assert len(client.get("/api/accuracy/by-hour").json()) == 24
    assert len(client.get("/api/accuracy/series").json()) == 744
    assert len(client.get("/api/accuracy/by-horizon").json()) >= 8
