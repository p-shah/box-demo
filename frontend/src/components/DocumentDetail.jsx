import { useEffect, useState } from 'react'
import { api } from '../api'
import SensitivityPill from './SensitivityPill'
import SummaryCard from './SummaryCard'
import HighlightsGrid from './HighlightsGrid'
import HoldingsDiffTable from './HoldingsDiffTable'
import ShareLinkCard from './ShareLinkCard'

function quarterSortKey(quarter) {
  const match = /^Q([1-4])-(\d{4})$/.exec(quarter || '')
  return match ? Number(match[2]) * 10 + Number(match[1]) : null
}

// Puts exactly two selected statements in chronological [from, to] order
// (by their detected quarter) so the diff table reads "what changed" left
// to right instead of depending on click order.
function chronologicalPair(documents) {
  if (documents.length !== 2) return documents
  const [a, b] = documents
  const keyA = quarterSortKey(a.metadata?.quarter)
  const keyB = quarterSortKey(b.metadata?.quarter)
  return keyA != null && keyB != null && keyB < keyA ? [b, a] : [a, b]
}

export default function DocumentDetail({ client, documents, onActivity }) {
  const [summaryCache, setSummaryCache] = useState({})
  const [highlightsCache, setHighlightsCache] = useState({})
  const [diffCache, setDiffCache] = useState({})

  const [summaryState, setSummaryState] = useState('idle')
  const [highlightsState, setHighlightsState] = useState('idle')
  const [diffState, setDiffState] = useState('idle')
  const [summaryError, setSummaryError] = useState(null)
  const [highlightsError, setHighlightsError] = useState(null)
  const [diffError, setDiffError] = useState(null)

  const selectionKey = documents
    .map((doc) => doc.id)
    .slice()
    .sort()
    .join(',')

  const isPair = documents.length === 2
  const orderedPair = chronologicalPair(documents)
  const diffKey = isPair ? orderedPair.map((doc) => doc.id).join('->') : null

  useEffect(() => {
    // A selection already analyzed once is served straight from cache — only
    // an unseen selection needs the "idle" (unrun) state. Without this check,
    // returning to a previously-run selection left state stuck at "idle"
    // while the run* functions below silently no-op on a cache hit, making
    // the "Generate"/"Extract"/"Compare" buttons appear to do nothing.
    setSummaryState(summaryCache[selectionKey] ? 'done' : 'idle')
    setHighlightsState(highlightsCache[selectionKey] ? 'done' : 'idle')
    setSummaryError(null)
    setHighlightsError(null)
    setDiffState(diffKey && diffCache[diffKey] ? 'done' : 'idle')
    setDiffError(null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectionKey, diffKey, summaryCache, highlightsCache, diffCache])

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

  const runDiff = () => {
    if (!isPair || diffCache[diffKey]) return
    setDiffState('loading')
    setDiffError(null)
    api
      .getHoldingsDiff({
        fileIds: orderedPair.map((doc) => doc.id),
        fileNames: orderedPair.map((doc) => doc.name),
        clientName: client.name,
      })
      .then((result) => {
        setDiffCache((prev) => ({ ...prev, [diffKey]: result }))
        setDiffState('done')
        onActivity()
      })
      .catch((err) => {
        setDiffError(err.message)
        setDiffState('error')
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

      <div className={`detail-columns${isMulti ? ' is-multi' : ''}`}>
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
          {isPair && (
            <HoldingsDiffTable
              state={diffState}
              error={diffError}
              data={diffCache[diffKey]}
              onRun={runDiff}
              fromLabel={orderedPair[0].metadata?.quarter || orderedPair[0].name}
              toLabel={orderedPair[1].metadata?.quarter || orderedPair[1].name}
            />
          )}
          {!isMulti && <ShareLinkCard document={documents[0]} client={client} onActivity={onActivity} />}
        </div>
      </div>
    </div>
  )
}
