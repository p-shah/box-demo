import { useEffect } from 'react'

export default function UploadStatus({ status, onDismiss }) {
  useEffect(() => {
    if (status.state === 'done') {
      const timer = setTimeout(onDismiss, 4000)
      return () => clearTimeout(timer)
    }
  }, [status, onDismiss])

  return (
    <div className={`upload-toast upload-toast-${status.state}`}>
      {status.state === 'pending' && (
        <>
          <span className="upload-toast-spinner" />
          <div>
            <div className="upload-toast-title">Classifying {status.fileName}</div>
            <div className="upload-toast-sub">Box AI is reading the document — usually ~10s</div>
          </div>
        </>
      )}
      {status.state === 'done' && (
        <div>
          <div className="upload-toast-title">{status.fileName} routed to {status.client}</div>
          <div className="upload-toast-sub">Classified, secured, and ready</div>
        </div>
      )}
      {status.state === 'error' && (
        <div>
          <div className="upload-toast-title">Upload failed</div>
          <div className="upload-toast-sub">{status.error}</div>
        </div>
      )}
      <button className="upload-toast-close" onClick={onDismiss} aria-label="Dismiss">
        ×
      </button>
    </div>
  )
}
