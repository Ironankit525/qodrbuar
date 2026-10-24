import { useState } from 'react'
import { formatMw } from '../format'

/**
 * Props (all MW):
 *  - averageWindMw: mean decision-time wind forecast for the selected delivery day
 *  - typicalErrorMw, biasMw: January forecast accuracy, shown so the result is not read as exact
 */
export function BuyingCalculator({ averageWindMw, typicalErrorMw, biasMw }) {
  const [demand, setDemand] = useState('')
  const demandMw = demand === '' ? undefined : Number(demand)
  const toBuyMw = demandMw === undefined ? undefined : Math.max(0, demandMw - averageWindMw)

  return (
    <section className="card">
      <h2>Power to buy for this day</h2>
      <p className="card-subtitle">
        Illustrative what-if: assumes the same demand in every hour. Power to buy = demand − expected wind.
      </p>

      <div className="calculator">
        <label>
          Expected demand (MW)
          <input
            type="number"
            min={0}
            step={100}
            placeholder="e.g. 30000"
            value={demand}
            onChange={(e) => setDemand(e.target.value)}
          />
        </label>
        <div className="calc-term">
          <span className="kpi-label">Expected wind</span>
          <span className="calc-value">{formatMw(averageWindMw)}</span>
        </div>
        <div className="calc-term result">
          <span className="kpi-label">Power to buy</span>
          <span className="calc-value">{toBuyMw === undefined ? '–' : formatMw(toBuyMw)}</span>
        </div>
      </div>

      {demandMw !== undefined && demandMw < averageWindMw && (
        <p className="calc-note">Expected wind exceeds this demand, so nothing is needed from other sources.</p>
      )}
      {typicalErrorMw !== undefined && biasMw !== undefined && (
        <p className="calc-note">
          This uses the raw forecast. In January it was typically off by ±{formatMw(typicalErrorMw)} and ran{' '}
          {formatMw(Math.abs(biasMw))} {biasMw > 0 ? 'too high' : 'too low'} on average, so plan for a margin of that
          size.
        </p>
      )}
    </section>
  )
}
