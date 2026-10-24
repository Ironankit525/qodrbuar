import { useState } from 'react'
import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { BuyingCalculator } from '../components/BuyingCalculator'
import { ChartCard } from '../components/ChartCard'
import { ChartTooltip } from '../components/ChartTooltip'
import { Kpi } from '../components/Kpi'
import { Status } from '../components/Status'
import { addDays, formatDateTime, formatMw, formatTime } from '../format'
import { useApi } from '../useApi'

const FORECAST_COLOR = 'var(--series-forecast)'
const ACTUAL_COLOR = 'var(--series-actual)'

/** Props: meta ({ first_delivery_date, last_delivery_date }) and cutoff ("HH:MM", UTC). */
export function ForecastView({ meta, cutoff }) {
  const [date, setDate] = useState(addDays(meta.first_delivery_date, 13))
  const [showActual, setShowActual] = useState(false)

  const forecast = useApi(`/api/forecast?delivery_date=${date}&cutoff=${cutoff}`)
  const accuracy = useApi(`/api/accuracy/summary?cutoff=${cutoff}`)

  const points = forecast.data?.points
  const typicalError = accuracy.data?.mae_mw
  const chartData = points?.map((p) => ({
    time: p.start_time,
    forecast: p.forecast_mw,
    actual: showActual ? p.actual_mw : null,
    band: typicalError === undefined ? null : [Math.max(0, p.forecast_mw - typicalError), p.forecast_mw + typicalError],
  }))

  const peak = points && points.reduce((best, p) => (p.forecast_mw > best.forecast_mw ? p : best))
  const average = points && points.reduce((sum, p) => sum + p.forecast_mw, 0) / points.length
  const latestPublish = points && points.reduce((latest, p) => (p.publish_time > latest ? p.publish_time : latest), '')

  return (
    <>
      <div className="toolbar">
        <div className="day-picker">
          <button
            type="button"
            className="day-step"
            aria-label="Previous day"
            disabled={date <= meta.first_delivery_date}
            onClick={() => setDate(addDays(date, -1))}
          >
            ←
          </button>
          <label>
            Delivery day
            <input
              type="date"
              value={date}
              min={meta.first_delivery_date}
              max={meta.last_delivery_date}
              onChange={(e) => e.target.value && setDate(e.target.value)}
            />
          </label>
          <button
            type="button"
            className="day-step"
            aria-label="Next day"
            disabled={date >= meta.last_delivery_date}
            onClick={() => setDate(addDays(date, 1))}
          >
            →
          </button>
        </div>
        <label className="check">
          <input type="checkbox" checked={showActual} onChange={(e) => setShowActual(e.target.checked)} />
          Show what actually happened
        </label>
      </div>

      <Status loading={forecast.loading} error={forecast.error} />
      {points && peak && average !== undefined && latestPublish && (
        <>
          <div className="kpis">
            <Kpi label="Expected wind (average)" value={formatMw(average)} hint="Mean of the 24 hourly forecasts" />
            <Kpi label="Peak wind" value={formatMw(peak.forecast_mw)} hint={`at ${formatTime(peak.start_time)} UTC`} />
            <Kpi
              label="Latest forecast available"
              value={formatDateTime(latestPublish)}
              hint={`UTC, before the ${cutoff} deadline`}
            />
            <Kpi
              label="Typical error"
              value={typicalError === undefined ? '…' : `± ${formatMw(typicalError)}`}
              hint="Average miss across January"
            />
          </div>

          <ChartCard
            title={`Wind forecast for ${formatDateTime(points[0].start_time).split(',')[0]}`}
            subtitle={`The forecast a trader would have had at ${cutoff} UTC the day before. Power bought from other sources = demand − wind.`}
            legend={[
              { label: 'Forecast (decision time)', color: FORECAST_COLOR },
              { label: 'Typical error range (±MAE)', color: FORECAST_COLOR, band: true },
              ...(showActual ? [{ label: 'Actual', color: ACTUAL_COLOR }] : []),
            ]}
            table={{
              columns: ['Hour (UTC)', 'Forecast (MW)', 'Published', 'Actual (MW)'],
              rows: points.map((p) => [
                formatTime(p.start_time),
                Math.round(p.forecast_mw),
                formatDateTime(p.publish_time),
                p.actual_mw === null ? '–' : Math.round(p.actual_mw),
              ]),
            }}
          >
            <ResponsiveContainer width="100%" height={340}>
              <ComposedChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
                <CartesianGrid stroke="var(--grid)" vertical={false} />
                <XAxis dataKey="time" tickFormatter={formatTime} tickLine={false} axisLine={false} minTickGap={24} />
                <YAxis tickFormatter={(v) => `${v / 1000} GW`} tickLine={false} axisLine={false} width={64} domain={[0, 'auto']} />
                <Tooltip
                  content={<ChartTooltip title={(t) => formatDateTime(String(t))} format={formatMw} />}
                  cursor={{ stroke: 'var(--text-muted)' }}
                />
                <Area dataKey="band" name="Typical range" fill={FORECAST_COLOR} fillOpacity={0.2} stroke="none" isAnimationActive={false} />
                <Line dataKey="forecast" name="Forecast" stroke={FORECAST_COLOR} strokeWidth={2} dot={false} isAnimationActive={false} />
                {showActual && (
                  <Line dataKey="actual" name="Actual" stroke={ACTUAL_COLOR} strokeWidth={2} dot={false} isAnimationActive={false} />
                )}
              </ComposedChart>
            </ResponsiveContainer>
          </ChartCard>

          <BuyingCalculator averageWindMw={average} typicalErrorMw={typicalError} biasMw={accuracy.data?.bias_mw} />
        </>
      )}
    </>
  )
}
