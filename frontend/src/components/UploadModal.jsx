import { useState } from 'react'

export default function UploadModal({ onClose, onSubmit }) {
  const [file, setFile] = useState(null)
  const [reportType, setReportType] = useState('Quarterly Statement')
  const [sensitivity, setSensitivity] = useState('Client Confidential')

  const submit = (e) => {
    e.preventDefault()
    if (!file) return
    // Classification takes several seconds (Box AI reading the document), so
    // hand off to the caller and close immediately rather than blocking here.
    onSubmit({ file, reportType, sensitivity })
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <div className="modal-title">Upload statement</div>

        <label className="field">
          <span>File</span>
          <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files[0])} required />
        </label>

        <label className="field">
          <span>Report type</span>
          <input value={reportType} onChange={(e) => setReportType(e.target.value)} />
        </label>

        <div className="field-note">
          Box AI reads the statement to detect the client and the quarter it covers — no
          need to enter either. If it's a new client, a folder is created automatically.
        </div>

        <label className="field">
          <span>Sensitivity</span>
          <select value={sensitivity} onChange={(e) => setSensitivity(e.target.value)}>
            <option>Client Confidential</option>
            <option>Confidential</option>
            <option>Internal</option>
            <option>Public</option>
          </select>
        </label>

        <div className="modal-actions">
          <button type="button" className="ghost-button" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="primary-button" disabled={!file}>
            Upload & classify
          </button>
        </div>
      </form>
    </div>
  )
}
