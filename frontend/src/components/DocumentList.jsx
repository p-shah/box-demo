import SensitivityPill from './SensitivityPill'

export default function DocumentList({
  client,
  documents,
  loading,
  selectedIds,
  onSelectOnly,
  onToggleSelected,
}) {
  return (
    <div className="panel">
      <div className="panel-heading">{client ? client.name : 'Documents'}</div>

      {loading && <div className="panel-empty">Loading documents…</div>}
      {!loading && client && documents.length === 0 && (
        <div className="panel-empty">No documents in this client's folder yet.</div>
      )}
      {selectedIds.size > 1 && (
        <div className="doc-list-hint">{selectedIds.size} selected — comparing across statements</div>
      )}

      <ul className="doc-list">
        {documents.map((doc) => {
          const checked = selectedIds.has(doc.id)
          return (
            <li key={doc.id}>
              <div className={`doc-list-item${checked ? ' is-selected' : ''}`}>
                <input
                  type="checkbox"
                  className="doc-list-checkbox"
                  checked={checked}
                  onChange={() => onToggleSelected(doc.id)}
                  onClick={(e) => e.stopPropagation()}
                  aria-label={`Include ${doc.name} in analysis`}
                />
                <button className="doc-list-item-body" onClick={() => onSelectOnly(doc.id)}>
                  <div className="doc-list-item-top">
                    <span className="doc-name">{doc.name}</span>
                    <SensitivityPill value={doc.metadata?.sensitivity} />
                  </div>
                  <div className="doc-list-item-meta">
                    {doc.metadata?.reportType || 'Report'}
                    {doc.metadata?.quarter ? ` · ${doc.metadata.quarter}` : ''}
                  </div>
                </button>
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
