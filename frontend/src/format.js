const number = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 0 })

export const formatMw = (mw) => `${number.format(mw)} MW`

export const formatSignedMw = (mw) => `${mw > 0 ? '+' : mw < 0 ? '−' : ''}${formatMw(Math.abs(mw))}`

export const formatPct = (pct) => `${pct.toFixed(1)}%`

const dateFormat = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' })
const timeFormat = new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' })

export const formatDay = (iso) => dateFormat.format(new Date(iso))
export const formatTime = (iso) => timeFormat.format(new Date(iso))
export const formatDateTime = (iso) => `${formatDay(iso)}, ${formatTime(iso)}`

/** "2026-01-15" + n days -> "2026-01-29" */
export function addDays(isoDate, days) {
  const date = new Date(`${isoDate}T00:00:00Z`)
  date.setUTCDate(date.getUTCDate() + days)
  return date.toISOString().slice(0, 10)
}
