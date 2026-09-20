export default function ClientList({ clients, error, selectedId, onSelect }) {
  return (
    <div className="panel">
      <div className="panel-heading">Clients</div>
      {error && <div className="panel-error">{error}</div>}
      {!error && clients.length === 0 && (
        <div className="panel-empty">No client folders found under the portal root.</div>
      )}
      <ul className="client-list">
        {clients.map((client) => (
          <li key={client.id}>
            <button
              className={`client-list-item${client.id === selectedId ? ' is-selected' : ''}`}
              onClick={() => onSelect(client)}
            >
              <span className="client-avatar">{initials(client.name)}</span>
              <span className="client-name">{client.name}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

function initials(name) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0].toUpperCase())
    .join('')
}
