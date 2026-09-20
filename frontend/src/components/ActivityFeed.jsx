export default function ActivityFeed({ entries, onRefresh }) {
  return (
    <div className="panel panel-grow">
      <div className="panel-heading">
        Audit Trail
        <button className="ghost-button" onClick={onRefresh} title="Refresh">
          ↻
        </button>
      </div>
      {entries.length === 0 && <div className="panel-empty">No activity yet this session.</div>}
      <ul className="activity-feed">
        {entries.map((entry, i) => (
          <li key={`${entry.timestamp}-${i}`} className="activity-item">
            <div className="activity-time">{formatTime(entry.timestamp)}</div>
            <div className="activity-text">
              <strong>{entry.action}</strong>
              <div className="activity-meta">
                {entry.file} · {entry.client}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}
