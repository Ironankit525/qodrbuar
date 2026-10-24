"""Thin client for the Elexon BMRS stream endpoints (FUELHH, WINDFOR)."""
import pandas as pd
import requests

from .config import ELEXON_BASE_URL

TIMEOUT_S = 120


def _stream(dataset: str, publish_from: str, publish_to: str, **params) -> list[dict]:
    resp = requests.get(
        f"{ELEXON_BASE_URL}/datasets/{dataset}/stream",
        params={"publishDateTimeFrom": publish_from, "publishDateTimeTo": publish_to, **params},
        timeout=TIMEOUT_S,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_actuals(publish_from: str, publish_to: str) -> pd.DataFrame:
    """Half-hourly national wind generation (MW). Columns: startTime, generation."""
    rows = _stream("FUELHH", publish_from, publish_to, fuelType="WIND")
    df = pd.DataFrame(rows, columns=["startTime", "fuelType", "generation"])
    df = df[df["fuelType"] == "WIND"].drop(columns="fuelType")
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    return df.drop_duplicates("startTime").sort_values("startTime").reset_index(drop=True)


def fetch_forecasts(publish_from: str, publish_to: str) -> pd.DataFrame:
    """Hourly wind forecasts (MW). Columns: startTime, publishTime, generation."""
    rows = _stream("WINDFOR", publish_from, publish_to)
    df = pd.DataFrame(rows, columns=["startTime", "publishTime", "generation"])
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    df = df.drop_duplicates(["startTime", "publishTime"])
    return df.sort_values(["startTime", "publishTime"]).reset_index(drop=True)
