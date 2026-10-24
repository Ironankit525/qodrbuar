# GB wind forecast monitor

A web app for a day-ahead power buyer. It answers two questions about national wind generation in Great Britain:

1. **What is the latest wind forecast available at the moment I have to decide?** (Day-ahead forecast tab)
2. **How accurate are those forecasts, in numbers?** (Forecast accuracy tab)

Data: Elexon BMRS only, national level, January 2026 decisions.
[`FUELHH`](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream) (actuals, `fuelType = WIND`) and
[`WINDFOR`](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream) (forecasts).

**Live app:** _to be added after deployment_ (hosted on Vercel, see [Deploy on Vercel](#deploy-on-vercel))

## Start the application

### With Docker (recommended)

```bash
docker compose up --build
```

Open <http://localhost:8080>. One container builds the React app and serves it together with the Python API.

Run the tests on the container's Python version (the build fails if a test fails):

```bash
docker build --target test .
```

### Without Docker (development)

Backend (Python 3.11+):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest                                   # tests
uvicorn app.main:app --port 8000                   # API, docs at /docs
```

Frontend (Node 22+), in a second terminal:

```bash
cd frontend
npm ci
npm run dev        # http://localhost:5173, proxies /api to http://127.0.0.1:8000
```

If the backend is on another port: `API_PROXY_TARGET=http://127.0.0.1:8765 npm run dev`.

The January 2026 data is committed in `backend/data/`, so no setup is needed. To re-download it from Elexon:
`cd backend && python -m scripts.ingest`.

## Deploy on Vercel

Vercel builds the container straight from the GitHub repo using `Dockerfile.vercel` (Vercel Container Runtime, beta).
`vercel.json` tells Vercel to deploy only that container as a single service and send all traffic to it (the
container already serves both the API and the website):

1. In Vercel choose **Add New → Project** and import this repository.
2. Under **Environment Variables** add `PORT` = `8000` (Vercel's default is port 80; the app listens on `$PORT`).
3. Deploy. Every push to `main` redeploys.

`Dockerfile.vercel` is a copy of `Dockerfile` (Vercel only looks for that exact name). The container is stateless and
scales to zero after a few minutes without traffic, so the first request after idle time can be slow.

## How it works

**Decision-time forecast.** WINDFOR publishes about 8 forecasts a day for the same target hours (`publishTime` differs).
A buyer deciding at a deadline can only use forecasts published before it. For each delivery hour the app picks
the **latest forecast with `publishTime` ≤ the deadline on the previous day** (default 09:20 UTC, adjustable in the UI).

**Accuracy.** That forecast is compared with the actual generation. Error = forecast − actual, so a positive error
means wind was over-forecast. Metrics: mean absolute error (MAE), RMSE, bias, 95th-percentile absolute error, and MAE
as a percentage of mean wind. They are also broken down by delivery day, hour of day and forecast lead time.

**Buying calculator.** On the Day-ahead tab: power to buy = demand − expected wind. Illustrative only; it uses one demand
figure for the whole day and the raw (uncorrected) forecast, and shows the January error next to the result.

### Assumptions and choices

- **Decision deadline: 09:20 UTC on the day before delivery.** The brief does not specify it. GB power for the next
  day is traded in two day-ahead auctions, which close at about 09:20 (EPEX SPOT) and 09:50 (Nord Pool N2EX) UK
  time, the same as UTC in January ([Nord Pool](https://support.nordpoolgroup.com/support/solutions/articles/8000088463-about-the-day-ahead-gb-auction),
  [Montel](https://montel.energy/assets/phil-hewitt---montel-analytics.pdf)). The default uses the earlier one, so the
  forecast shown is one the buyer really had for either auction. Other morning deadlines give similar results (MAE
  2.0 GW for any deadline from 06:00 to 11:00); a later deadline such as 12:00 would wrongly use the 11:30 forecast.
- **Delivery days 2 Jan – 1 Feb 2026** (744 hours): the delivery days for decisions made in January.
- **Hourly comparison.** WINDFOR is hourly and FUELHH half-hourly, so actuals are averaged over the two half-hours of
  each hour; hours missing either half-hour are dropped.
- **Back-filled forecasts.** WINDFOR also returns values for hours already past at publish time (negative lead time).
  The lead-time analysis only uses genuine forecasts (lead time ≥ 0).
- **All times are UTC** (equal to UK time in January).
- **Data is stored locally** (Parquet) rather than fetched per request: the scope is a fixed month, so the app is fast
  and does not depend on Elexon being reachable.

### Findings for January 2026 (09:20 deadline)

| Metric | Value |
|---|---|
| Mean absolute error | 2,039 MW (18.1% of mean wind) |
| RMSE | 2,505 MW |
| Bias | +1,748 MW (forecast too high; over-forecast in 85% of hours) |
| 95th-percentile absolute error | 5,283 MW |

Error grows with lead time (about 1.7 GW under 6 h ahead to about 2.4 GW at 60 h+). These are one month of data and
the cause of the bias has not been investigated; treat them as pilot findings, not general rules.

## Files and directories

```
.
├── Dockerfile               Multi-stage build: React build, Python runtime, optional `test` target
├── Dockerfile.vercel        Same as Dockerfile; the name Vercel looks for
├── vercel.json              Vercel config: deploy the container as the only service
├── docker-compose.yml       `docker compose up` -> http://localhost:8080
├── .dockerignore
├── .gitignore
├── backend/
│   ├── requirements.txt     Runtime dependencies (pinned)
│   ├── requirements-dev.txt Adds pytest and httpx
│   ├── app/
│   │   ├── main.py          FastAPI app; also serves the built frontend when present
│   │   ├── routes.py        /api endpoints
│   │   ├── schemas.py       Pydantic response models
│   │   ├── analysis.py      Decision-time selection and error metrics (pure functions)
│   │   ├── data.py          Loads the delivery-window data once, in memory
│   │   ├── repository.py    Parquet storage
│   │   ├── elexon_client.py Elexon BMRS API client (used by ingest)
│   │   └── config.py        Paths, delivery window, default deadline
│   ├── scripts/ingest.py    Downloads data from Elexon into backend/data/
│   ├── data/                actuals.parquet, forecasts.parquet (January 2026)
│   └── tests/               pytest: analysis logic, API, storage
└── frontend/
    ├── package.json, vite.config.js, .oxlintrc.json
    ├── index.html, public/favicon.svg
    └── src/
        ├── main.jsx         Entry point
        ├── App.jsx          Tabs and the decision-deadline control
        ├── api.js           API client; documents the response shapes
        ├── useApi.js        Data-fetching hook
        ├── format.js        Number, date and unit formatting
        ├── index.css        Styles and light/dark colour tokens
        ├── views/           ForecastView.jsx, AccuracyView.jsx
        └── components/      Kpi, ChartCard, ChartTooltip, Status, BuyingCalculator
```

### API

| Endpoint | Returns |
|---|---|
| `GET /api/meta` | Delivery date range and default deadline |
| `GET /api/forecast?delivery_date=&cutoff=` | The decision-time forecast for each hour of a day, with the actual when available |
| `GET /api/accuracy/summary?cutoff=` | Overall metrics |
| `GET /api/accuracy/series?cutoff=` | Hourly forecast vs actual for the whole window |
| `GET /api/accuracy/daily?cutoff=` | Metrics per delivery day |
| `GET /api/accuracy/by-hour?cutoff=` | Metrics per hour of day |
| `GET /api/accuracy/by-horizon` | Metrics by forecast lead time (all forecasts; independent of the deadline) |

`cutoff` is `HH:MM` (UTC) on the day before delivery; default `09:20`. Interactive docs at `/docs`.

## Tests

- Backend: 13 pytest tests. Analysis logic is tested on small hand-made data (including deadline boundaries and
  back-filled forecasts); the API is tested against the stored data.
- Frontend: React (JavaScript), linted with `oxlint` (including React hook rules); no automated UI tests in the repo.
  Every feature was checked in a browser against the Docker container, in light and dark mode and at phone width.
- The headline numbers were also recomputed independently from the raw Elexon responses with separate plain-Python
  code and matched the app exactly.

## Use of AI tools

I used Claude (Anthropic), through the Claude Code agent, to build this project. I used it to research the Elexon
data (FUELHH and WINDFOR), to write and review the code for both the Python backend and the React frontend, and to
write the tests and this README. I directed the work, decided what the app should show and which features to add (for
example the buying calculator and the day-by-day navigation), and reviewed the result in the browser. The assumptions
above and the numbers in the findings were checked against the raw Elexon data as described under Tests.
