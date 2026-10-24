import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ChartCard } from '../components/ChartCard'
import { ChartTooltip } from '../components/ChartTooltip'
import { Kpi } from '../components/Kpi'
import { Status } from '../components/Status'
import { formatDay, formatDateTime, formatMw, formatPct, formatSignedMw } from '../format'
import { useApi } from '../useApi'

const FORECAST_COLOR = 'var(--series-forecast)'
const ACTUAL_COLOR = 'var(--series-actual)'
const CURSOR = { fill: 'var(--grid)' }
const gw = (v) => `${v / 1000} GW`

export function AccuracyView({ cutoff }) {
  const summary = useApi(`/api/accuracy/summary?cutoff=${cutoff}`)
  const series = useApi(`/api/accuracy/series?cutoff=${cutoff}`)
  const daily = useApi(`/api/accuracy/daily?cutoff=${cutoff}`)
  const byHour = useApi(`/api/accuracy/by-hour?cutoff=${cutoff}`)
  const byHorizon = useApi('/api/accuracy/by-horizon')

  const error = summary.error ?? series.error ?? daily.error ?? byHour.error ?? byHorizon.error
  const m = summary.data
  if (!m) return <Status loading={summary.loading} error={error} />

  const direction = m.bias_mw > 0 ? 'over-forecast' : 'under-forecast'
  return (
    <>
      <div className="kpis">
        <Kpi label="Mean absolute error" value={formatMw(m.mae_mw)} hint={`${formatPct(m.nmae_pct)} of average wind`} />
        <Kpi label="RMSE" value={formatMw(m.rmse_mw)} hint="Penalises large misses" />
        <Kpi label="Bias" value={formatSignedMw(m.bias_mw)} hint={`Wind was ${direction} on average`} />
        <Kpi label="95th percentile error" value={formatMw(m.p95_abs_error_mw)} hint="Only 1 hour in 20 is worse" />
      </div>

      <div className="insight">
        <strong>What this means for buying:</strong> across {m.n} delivery hours in January, forecasts available at{' '}
        {cutoff} UTC the day before missed by {formatMw(m.mae_mw)} on average and were {direction} by{' '}
        {formatMw(Math.abs(m.bias_mw))} on average. Keeping a buffer of about {formatMw(m.p95_abs_error_mw)} would
        have covered 19 hours in 20.
      </div>

      {series.data && (
        <ChartCard
          title="Forecast vs actual wind generation"
          subtitle="Hourly, 2 Jan – 1 Feb 2026. The forecast is the one available at the decision deadline."
          legend={[
            { label: 'Forecast (decision time)', color: FORECAST_COLOR },
            { label: 'Actual', color: ACTUAL_COLOR },
          ]}
        >
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={series.data} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
              <CartesianGrid stroke="var(--grid)" vertical={false} />
              <XAxis dataKey="start_time" tickFormatter={formatDay} tickLine={false} axisLine={false} minTickGap={48} />
              <YAxis tickFormatter={gw} tickLine={false} axisLine={false} width={64} />
              <Tooltip
                content={<ChartTooltip title={(t) => formatDateTime(String(t))} format={formatMw} />}
                cursor={{ stroke: 'var(--text-muted)' }}
              />
              <Line dataKey="forecast_mw" name="Forecast" stroke={FORECAST_COLOR} strokeWidth={1.5} dot={false} isAnimationActive={false} />
              <Line dataKey="actual_mw" name="Actual" stroke={ACTUAL_COLOR} strokeWidth={1.5} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      )}

      {daily.data && (
        <ChartCard
          title="Error by delivery day"
          subtitle="Mean absolute error per day. Some days are much harder to forecast than others."
          table={{
            columns: ['Day', 'MAE (MW)', 'Bias (MW)'],
            rows: daily.data.map((d) => [d.date, Math.round(d.mae_mw), Math.round(d.bias_mw)]),
          }}
        >
          <MaeBars data={daily.data} xKey="date" xFormat={(d) => formatDay(String(d))} tooltipTitle={(d) => formatDay(String(d))} />
        </ChartCard>
      )}

      <div className="grid-2">
        {byHorizon.data && (
          <ChartCard
            title="Error by forecast lead time"
            subtitle="How far ahead of the delivery hour the forecast was published. Includes every forecast, not just the decision-time one."
            table={{
              columns: ['Lead time', 'MAE (MW)', 'Bias (MW)'],
              rows: byHorizon.data.map((h) => [horizonLabel(h.horizon_from_h), Math.round(h.mae_mw), Math.round(h.bias_mw)]),
            }}
          >
            <MaeBars
              data={byHorizon.data}
              xKey="horizon_from_h"
              xFormat={(h) => `${h}h`}
              tooltipTitle={(h) => `${horizonLabel(Number(h))} ahead`}
            />
          </ChartCard>
        )}
        {byHour.data && (
          <ChartCard
            title="Error by hour of day"
            subtitle="Mean absolute error for each delivery hour (UTC)."
            table={{
              columns: ['Hour (UTC)', 'MAE (MW)', 'Bias (MW)'],
              rows: byHour.data.map((h) => [`${String(h.hour).padStart(2, '0')}:00`, Math.round(h.mae_mw), Math.round(h.bias_mw)]),
            }}
          >
            <MaeBars
              data={byHour.data}
              xKey="hour"
              xFormat={(h) => String(h).padStart(2, '0')}
              tooltipTitle={(h) => `${String(h).padStart(2, '0')}:00 UTC`}
            />
          </ChartCard>
        )}
      </div>
      <Status loading={false} error={error} />
    </>
  )
}

const horizonLabel = (from) => `${from}–${from + 6}h`

/** Bar chart of mean absolute error. xFormat and tooltipTitle format the x value (axis tick and tooltip heading). */
function MaeBars({ data, xKey, xFormat, tooltipTitle }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
        <CartesianGrid stroke="var(--grid)" vertical={false} />
        <XAxis dataKey={xKey} tickFormatter={xFormat} tickLine={false} axisLine={false} minTickGap={12} />
        <YAxis tickFormatter={gw} tickLine={false} axisLine={false} width={64} />
        <Tooltip content={<ChartTooltip title={tooltipTitle} format={formatMw} />} cursor={CURSOR} />
        <Bar dataKey="mae_mw" name="Mean absolute error" fill={FORECAST_COLOR} radius={[4, 4, 0, 0]} maxBarSize={28} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  )
}
