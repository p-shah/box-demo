const TILES = [
  { key: 'beginningValue', label: 'Beginning Value' },
  { key: 'endingValue', label: 'Ending Value' },
  { key: 'netMarketGain', label: 'Net Market Gain', signed: true },
  { key: 'topHolding', label: 'Largest Holding' },
]

export default function HighlightsGrid({ state, error, data, onRun }) {
  return (
    <div className="card">
      <div className="card-heading">
        <div>
          <div className="card-title">Financial Highlights</div>
          <div className="card-subtitle">Box AI structured extraction, straight from the PDF</div>
        </div>
        {state === 'idle' && (
          <button className="primary-button small" onClick={onRun}>
            Extract with Box AI
          </button>
        )}
        {state === 'loading' && <span className="card-status">Extracting…</span>}
      </div>

      {state === 'error' && <div className="card-error">{error}</div>}

      {state === 'done' && data && (
        <>
          <div className="stat-grid">
            {TILES.map((tile) => (
              <StatTile key={tile.key} label={tile.label} value={data[tile.key]} signed={tile.signed} />
            ))}
          </div>
          {data.performanceDriver && (
            <div className="highlight-note">
              <span className="highlight-note-label">Performance driver</span>
              {data.performanceDriver}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function StatTile({ label, value, signed }) {
  const negative = signed && typeof value === 'string' && /^-|^\(/.test(value.trim())
  const tone = signed ? (negative ? 'critical' : 'good') : 'neutral'
  return (
    <div className="stat-tile">
      <div className="stat-tile-label">{label}</div>
      <div className={`stat-tile-value stat-tile-${tone}`}>
        {signed && !negative && value ? '▲ ' : signed && negative ? '▼ ' : ''}
        {value || '—'}
      </div>
    </div>
  )
}
