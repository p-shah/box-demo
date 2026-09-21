import { useEffect, useRef, useState } from 'react'
import { api } from '../api'

export default function SearchBar({ onSelect }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [state, setState] = useState('idle') // idle | loading | done | error
  const [open, setOpen] = useState(false)
  const debounceRef = useRef(null)

  const runSearch = (q) => {
    if (!q.trim()) {
      setResults([])
      setState('idle')
      return
    }
    setState('loading')
    api
      .search(q)
      .then((matches) => {
        setResults(matches)
        setState('done')
      })
      .catch(() => {
        setResults([])
        setState('error')
      })
  }

  useEffect(() => {
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => runSearch(query), 350)
    return () => clearTimeout(debounceRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query])

  const handleSelect = (result) => {
    setOpen(false)
    setQuery('')
    setResults([])
    onSelect(result)
  }

  return (
    <div className="search-bar">
      <input
        className="search-input"
        type="search"
        placeholder="Search all clients & statements…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') runSearch(query)
          if (e.key === 'Escape') setOpen(false)
        }}
      />

      {open && query.trim() && (
        <div className="search-results">
          {state === 'loading' && <div className="search-results-empty">Searching…</div>}
          {state === 'error' && <div className="search-results-empty">Search failed. Try again.</div>}
          {state === 'done' && results.length === 0 && (
            <div className="search-results-empty">No matches for "{query}".</div>
          )}
          {results.map((result) => (
            <button
              key={result.id}
              className="search-result-item"
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => handleSelect(result)}
            >
              <span className="search-result-name">{result.name}</span>
              <span className="search-result-client">{result.client?.name || 'Unsorted'}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
