/**
 * Tooltip for Recharts. `active`, `payload` and `label` are injected by Recharts;
 * `title(label)` and `format(value)` are ours.
 */
export function ChartTooltip({ active, payload, label, title, format }) {
  if (!active || !payload?.length || label === undefined) return null
  const rows = [...payload].sort((a, b) => Number(Array.isArray(a.value)) - Number(Array.isArray(b.value)))
  return (
    <div className="tooltip">
      <div className="tooltip-title">{title(label)}</div>
      {rows.map((entry) => (
        <div className="tooltip-row" key={entry.name}>
          <span className="swatch" style={{ background: entry.color }} />
          {entry.name}
          <b>{formatValue(entry.value, format)}</b>
        </div>
      ))}
    </div>
  )
}

/** Plain values are formatted directly; range series (e.g. the error band) arrive as [low, high]. */
function formatValue(value, format) {
  if (Array.isArray(value)) return `${format(value[0])} – ${format(value[1])}`
  return format(Number(value))
}
