// Response shapes (see backend/app/schemas.py). Times are ISO-8601 UTC strings, power is in MW.
//
//   Meta         { first_delivery_date, last_delivery_date, default_cutoff }
//   DayForecast  { delivery_date, cutoff, points: [{ start_time, forecast_mw, publish_time, horizon_hours, actual_mw | null }] }
//   SeriesPoint  { start_time, forecast_mw, actual_mw }
//   Metrics      { n, mean_actual_mw, bias_mw, mae_mw, rmse_mw, p95_abs_error_mw, nmae_pct }
//                (+ date / hour / horizon_from_h for the per-day, per-hour and per-lead-time endpoints)

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

export async function getJson(path) {
  const response = await fetch(`${BASE_URL}${path}`)
  if (!response.ok) {
    const detail = await response.json().then((body) => body.detail, () => response.statusText)
    throw new Error(typeof detail === 'string' ? detail : response.statusText)
  }
  return response.json()
}
