import { useState } from 'react'
import { Status } from './components/Status'
import { AccuracyView } from './views/AccuracyView'
import { ForecastView } from './views/ForecastView'
import { useApi } from './useApi'

const TABS = [
  { id: 'forecast', label: 'Day-ahead forecast' },
  { id: 'accuracy', label: 'Forecast accuracy' },
]

export default function App() {
  const meta = useApi('/api/meta')
  const [tab, setTab] = useState('forecast')
  const [cutoffOverride, setCutoffOverride] = useState()

  const cutoff = cutoffOverride ?? meta.data?.default_cutoff

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>GB wind forecast monitor</h1>
          <p>Day-ahead wind generation forecasts vs actuals · national level · January 2026</p>
        </div>
        <label className="cutoff">
          Decision deadline (UTC, day before delivery)
          <input
            type="time"
            value={cutoff ?? ''}
            onChange={(e) => e.target.value && setCutoffOverride(e.target.value)}
          />
        </label>
      </header>

      <div className="tabs" role="tablist">
        {TABS.map(({ id, label }) => (
          <button key={id} className="tab" role="tab" aria-selected={tab === id} onClick={() => setTab(id)}>
            {label}
          </button>
        ))}
      </div>

      {meta.data && cutoff ? (
        tab === 'forecast' ? <ForecastView meta={meta.data} cutoff={cutoff} /> : <AccuracyView cutoff={cutoff} />
      ) : (
        <Status loading={meta.loading} error={meta.error} />
      )}
    </div>
  )
}
