/**
 * A titled card around a chart.
 *  - legend: [{ label, color, band? }]
 *  - table:  { columns: string[], rows: (string | number)[][] }, the accessible "View as table" alternative
 */
export function ChartCard({ title, subtitle, legend, table, children }) {
  return (
    <section className="card">
      <h2>{title}</h2>
      <p className="card-subtitle">{subtitle}</p>
      {legend && (
        <ul className="legend">
          {legend.map((item) => (
            <li key={item.label}>
              <span className={item.band ? 'swatch band' : 'swatch'} style={{ background: item.color }} />
              {item.label}
            </li>
          ))}
        </ul>
      )}
      {children}
      {table && (
        <details className="table-view">
          <summary>View as table</summary>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>{table.columns.map((c) => <th key={c}>{c}</th>)}</tr>
              </thead>
              <tbody>
                {table.rows.map((row) => (
                  <tr key={row[0]}>{row.map((cell, i) => <td key={i}>{cell}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </section>
  )
}
