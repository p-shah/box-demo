const STATUS_LABEL = {
  new: 'New',
  removed: 'Removed',
  increased: 'Up',
  decreased: 'Down',
  unchanged: 'Unchanged',
}

const STATUS_TONE = {
  new: 'good',
  removed: 'critical',
  increased: 'good',
  decreased: 'critical',
  unchanged: 'muted',
}

export default function HoldingsDiffTable({ state, error, data, onRun, fromLabel, toLabel }) {
  const rows = data?.rows || []

  return (
    <div className="card">
      <div className="card-heading">
        <div>
          <div className="card-title">Holdings Changes</div>
          <div className="card-subtitle">
            {fromLabel && toLabel ? `${fromLabel} → ${toLabel}` : 'What changed between these statements'}
          </div>
        </div>
        {state === 'idle' && (
          <button className="primary-button small" onClick={onRun}>
            Compare with Box AI
          </button>
        )}
        {state === 'loading' && <span className="card-status">Comparing…</span>}
      </div>

      {state === 'error' && <div className="card-error">{error}</div>}

      {state === 'done' && rows.length === 0 && (
        <div className="card-empty">No holdings could be read from these statements.</div>
      )}

      {state === 'done' && rows.length > 0 && (
        <div className="diff-table-scroll">
          <table className="diff-table">
            <thead>
              <tr>
                <th>Asset</th>
                <th>Shares</th>
                <th>Value</th>
                <th>Change</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={`${row.ticker || row.asset}-${i}`}>
                  <td>
                    <div className="diff-asset-name">{row.asset}</div>
                    {row.ticker && <div className="diff-asset-ticker">{row.ticker}</div>}
                  </td>
                  <td className="diff-numeric">
                    {formatShares(row.sharesFrom)} → {formatShares(row.sharesTo)}
                  </td>
                  <td className="diff-numeric">
                    {formatMoney(row.valueFrom)} → {formatMoney(row.valueTo)}
                  </td>
                  <td className="diff-numeric">
                    <span className={`pill pill-${STATUS_TONE[row.status]}`}>{STATUS_LABEL[row.status]}</span>
                    {row.valueDelta != null && (
                      <div className={`diff-delta diff-delta-${row.valueDelta >= 0 ? 'good' : 'critical'}`}>
                        {row.valueDelta >= 0 ? '▲ ' : '▼ '}
                        {formatMoney(Math.abs(row.valueDelta))}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function formatMoney(value) {
  if (value == null) return '—'
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatShares(value) {
  if (value == null) return '—'
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 })
}
