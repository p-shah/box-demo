import { useState } from 'react'
import { api } from '../api'

export default function ShareLinkCard({ document, client, onActivity }) {
  const [state, setState] = useState('idle')
  const [link, setLink] = useState(null)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)

  const createLink = () => {
    setState('loading')
    setError(null)
    api
      .createShareLink(document.id, { fileName: document.name, clientName: client.name, daysValid: 14 })
      .then((result) => {
        setLink(result)
        setState('done')
        onActivity()
      })
      .catch((err) => {
        setError(err.message)
        setState('error')
      })
  }

  const copyLink = () => {
    navigator.clipboard?.writeText(link.url).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  return (
    <div className="card">
      <div className="card-heading">
        <div>
          <div className="card-title">Secure Client Access</div>
          <div className="card-subtitle">View-only link, download disabled, auto-expiring</div>
        </div>
        {state === 'idle' && (
          <button className="primary-button small" onClick={createLink}>
            Create link
          </button>
        )}
        {state === 'loading' && <span className="card-status">Creating…</span>}
      </div>

      {state === 'error' && <div className="card-error">{error}</div>}

      {state === 'done' && link && (
        <div className="share-row">
          <input className="share-input" readOnly value={link.url} onFocus={(e) => e.target.select()} />
          <button className="ghost-button" onClick={copyLink}>
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      )}
      {state === 'done' && link && (
        <div className="share-expiry">Expires {new Date(link.expiresAt).toLocaleDateString()}</div>
      )}
    </div>
  )
}
