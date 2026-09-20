import { useEffect, useState } from 'react'
import { api } from '../api'
import SensitivityPill from './SensitivityPill'
import SummaryCard from './SummaryCard'
import HighlightsGrid from './HighlightsGrid'
import ShareLinkCard from './ShareLinkCard'

export default function DocumentDetail({ client, documents, onActivity }) {
  const [summaryCache, setSummaryCache] = useState({})
  const [highlightsCache, setHighlightsCache] = useState({})

  const [summaryState, setSummaryState] = useState('idle')
  const [highlightsState, setHighlightsState] = useState('idle')
  const [summaryError, setSummaryError] = useState(null)
  const [highlightsError, setHighlightsError] = useState(null)

  const selectionKey = documents
    .map((doc) => doc.id)
    .slice()
    .sort()
    .join(',')

  useEffect(() => {
    setSummaryState('idle')
    setHighlightsState('idle')
    setSummaryError(null)
    setHighlightsError(null)
  }, [selectionKey])

  if (!client || documents.length === 0) {
    return (
      <div className="detail-empty">
        <div className="detail-empty-title">Select a document</div>
        <div className="detail-empty-sub">
          Choose a client and statement to preview it and run Box AI. Check multiple
          statements to compare them together.
        </div>
      </div>
    )
  }

  const isMulti = documents.length > 1
  const fileIds = documents.map((doc) => doc.id)
  const fileNames = documents.map((doc) => doc.name)
  const contextArgs = { fileIds, fileNames, clientName: client.name }

  const runSummary = () => {
    if (summaryCache[selectionKey]) return
    setSummaryState('loading')
    setSummaryError(null)
    api
      .getSummary(contextArgs)
      .then((result) => {
        setSummaryCache((prev) => ({ ...prev, [selectionKey]: result }))
        setSummaryState('done')
        onActivity()
      })
      .catch((err) => {
        setSummaryError(err.message)
        setSummaryState('error')
      })
  }

  const runHighlights = () => {
    if (highlightsCache[selectionKey]) return
    setHighlightsState('loading')
    setHighlightsError(null)
    api
      .getHighlights(contextArgs)
      .then((result) => {
        setHighlightsCache((prev) => ({ ...prev, [selectionKey]: result }))
        setHighlightsState('done')
        onActivity()
      })
      .catch((err) => {
        setHighlightsError(err.message)
        setHighlightsState('error')
      })
  }

  return (
    <div className="detail">
      <div className="detail-header">
        <div>
          <div className="detail-title">
            {isMulti ? `${documents.length} statements selected` : documents[0].name}
          </div>
          <div className="detail-subtitle">
            {isMulti
              ? `${fileNames.join(', ')} · ${client.name}`
              : `${documents[0].metadata?.reportType || 'Report'}${
                  documents[0].metadata?.quarter ? ` · ${documents[0].metadata.quarter}` : ''
                } · ${client.name}`}
          </div>
        </div>
        {!isMulti && <SensitivityPill value={documents[0].metadata?.sensitivity} />}
      </div>

      <div className="detail-columns">
        {isMulti ? (
          <div className="detail-multi-list">
            <div className="detail-multi-hint">
              Box AI is reading all {documents.length} statements together for the panels on
              the right.
            </div>
            <ul className="detail-multi-items">
              {documents.map((doc) => (
                <li key={doc.id} className="detail-multi-item">
                  <span className="doc-name">{doc.name}</span>
                  <span className="doc-list-item-meta">
                    {doc.metadata?.reportType || 'Report'}
                    {doc.metadata?.quarter ? ` · ${doc.metadata.quarter}` : ''}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="detail-viewer">
            <iframe
              title={documents[0].name}
              src={api.documentContentUrl(documents[0].id, documents[0].name)}
              className="pdf-frame"
            />
          </div>
        )}

        <div className="detail-side">
          <HighlightsGrid
            state={highlightsState}
            error={highlightsError}
            data={highlightsCache[selectionKey]}
            onRun={runHighlights}
          />
          <SummaryCard
            state={summaryState}
            error={summaryError}
            data={summaryCache[selectionKey]}
            onRun={runSummary}
          />
          {!isMulti && <ShareLinkCard document={documents[0]} client={client} onActivity={onActivity} />}
        </div>
      </div>
    </div>
  )
}
