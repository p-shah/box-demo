function cleanLine(raw) {
  return raw
    .replace(/\*/g, '') // markdown emphasis/bullet asterisks (bold, italic, "* item")
    .replace(/^#+\s*/, '') // markdown headings
    .replace(/^[-•]\s*/, '') // dash/bullet markers
    .replace(/^\d+\.\s*/, '') // numbered list markers
    .trim()
}

export default function SummaryCard({ state, error, data, onRun }) {
  const bullets = data?.summary
    ? data.summary
        .split(/\n+/)
        .map(cleanLine)
        .filter(Boolean)
    : []

  // Box AI is prompted not to, but sometimes still closes with a
  // conversational follow-up ("Want talking points for this?") — there's no
  // chat to reply in here, so drop it if it shows up as the last line.
  if (bullets.length > 1 && /\?\s*$/.test(bullets[bullets.length - 1])) {
    bullets.pop()
  }

  return (
    <div className="card">
      <div className="card-heading">
        <div>
          <div className="card-title">Advisor Briefing</div>
          <div className="card-subtitle">Box AI summary, ready before the client call</div>
        </div>
        {state === 'idle' && (
          <button className="primary-button small" onClick={onRun}>
            Generate with Box AI
          </button>
        )}
        {state === 'loading' && <span className="card-status">Thinking…</span>}
      </div>

      {state === 'error' && <div className="card-error">{error}</div>}

      {state === 'done' && (
        <ul className="briefing-list">
          {bullets.map((line, i) => (
            <li key={i}>{line}</li>
          ))}
        </ul>
      )}

      {state === 'done' && data?.citations?.length > 0 && (
        <div className="citation-row">
          Grounded in: {data.citations.map((c) => c.name).filter(Boolean).join(', ') || 'source document'}
        </div>
      )}
    </div>
  )
}
