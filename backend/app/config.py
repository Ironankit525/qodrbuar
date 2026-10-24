import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
# Built React app; only present in the Docker image, where the API serves it.
STATIC_DIR = Path(os.getenv("STATIC_DIR", BASE_DIR / "static"))

ELEXON_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

# Decisions made 1-31 Jan 2026 are for delivery days 2 Jan - 1 Feb (end is exclusive).
DELIVERY_START = "2026-01-02T00:00:00Z"
DELIVERY_END = "2026-02-02T00:00:00Z"

# Day-ahead decision deadline: time of day (UTC) on the day before delivery. 09:20 is when the
# earlier of the two GB day-ahead auctions (EPEX SPOT) closes; N2EX closes at 09:50.
DEFAULT_CUTOFF = "09:20"

# Ingestion windows (by Elexon publish time). Forecasts start earlier so that
# the first delivery day has forecasts published the day before.
ACTUALS_PUBLISH_FROM = "2026-01-01T00:00:00Z"
ACTUALS_PUBLISH_TO = "2026-02-02T00:00:00Z"
FORECASTS_PUBLISH_FROM = "2025-12-30T00:00:00Z"
FORECASTS_PUBLISH_TO = "2026-02-01T00:00:00Z"
