import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from './api'
import ClientList from './components/ClientList'
import DocumentList from './components/DocumentList'
import DocumentDetail from './components/DocumentDetail'
import ActivityFeed from './components/ActivityFeed'
import UploadModal from './components/UploadModal'
import UploadStatus from './components/UploadStatus'
import SearchBar from './components/SearchBar'
import './App.css'

export default function App() {
  const [clients, setClients] = useState([])
  const [clientsError, setClientsError] = useState(null)
  const [selectedClient, setSelectedClient] = useState(null)

  const [documents, setDocuments] = useState([])
  const [documentsLoading, setDocumentsLoading] = useState(false)
  const [selectedIds, setSelectedIds] = useState(new Set())

  const [activity, setActivity] = useState([])
  const [uploadOpen, setUploadOpen] = useState(false)
  const [pendingUpload, setPendingUpload] = useState(null)
  const pendingDocIdRef = useRef(null)

  const refreshActivity = useCallback(() => {
    api.getActivity().then(setActivity).catch(() => {})
  }, [])

  const refreshClients = useCallback(() => {
    api.listClients().then(setClients).catch((err) => setClientsError(err.message))
  }, [])

  useEffect(() => {
    api
      .listClients()
      .then((list) => {
        setClients(list)
        if (list.length) setSelectedClient(list[0])
      })
      .catch((err) => setClientsError(err.message))
    refreshActivity()
  }, [refreshActivity])

  const loadDocuments = useCallback((client) => {
    if (!client) return
    setDocumentsLoading(true)
    setSelectedIds(new Set())
    api
      .listDocuments(client.id)
      .then((docs) => {
        setDocuments(docs)
        // A search result click stashes the doc it wants selected here —
        // land on that one instead of defaulting to the first document.
        const pendingId = pendingDocIdRef.current
        pendingDocIdRef.current = null
        const target = pendingId && docs.find((doc) => doc.id === pendingId)
        setSelectedIds(new Set(target ? [target.id] : docs.length ? [docs[0].id] : []))
      })
      .catch(() => setDocuments([]))
      .finally(() => setDocumentsLoading(false))
  }, [])

  useEffect(() => {
    loadDocuments(selectedClient)
  }, [selectedClient, loadDocuments])

  const selectOnly = (docId) => setSelectedIds(new Set([docId]))

  const toggleSelected = (docId) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(docId)) next.delete(docId)
      else next.add(docId)
      return next
    })
  }

  // Uploading (dominated by Box AI reading the document, ~10s) runs in the
  // background instead of blocking a modal — the modal closes immediately
  // and a dismissible status pill tracks progress so the advisor can keep
  // working while it classifies and routes the file.
  const startUpload = ({ file, reportType, sensitivity }) => {
    setUploadOpen(false)
    setPendingUpload({ fileName: file.name, state: 'pending' })
    api
      .uploadDocument({ file, reportType, sensitivity })
      .then((result) => {
        setPendingUpload({ fileName: file.name, state: 'done', client: result.client.name })
        refreshActivity()
        refreshClients()
        if (selectedClient?.id === result.client.id) {
          loadDocuments(selectedClient)
        }
      })
      .catch((err) => {
        setPendingUpload({ fileName: file.name, state: 'error', error: err.message })
      })
  }

  const handleSearchSelect = (result) => {
    if (!result.client) return
    pendingDocIdRef.current = result.id
    setSelectedClient({ id: result.client.id, name: result.client.name })
  }

  const selectedDocuments = documents.filter((doc) => selectedIds.has(doc.id))

  return (
    <div className="portal">
      <header className="portal-topbar">
        <div className="portal-brand">
          <span className="portal-brand-mark">SC</span>
          <div>
            <div className="portal-brand-title">Secure Client Reporting Portal</div>
            <div className="portal-brand-subtitle">Wealth Management Digital Experience</div>
          </div>
        </div>
        <SearchBar onSelect={handleSearchSelect} />
        <div className="portal-topbar-actions">
          <button className="primary-button" onClick={() => setUploadOpen(true)}>
            + Upload statement
          </button>
          <div className="portal-ai-badge">
            <span className="portal-ai-dot" />
            Powered by Box AI
          </div>
        </div>
      </header>

      <div className="portal-body">
        <aside className="portal-rail">
          <ClientList
            clients={clients}
            error={clientsError}
            selectedId={selectedClient?.id}
            onSelect={setSelectedClient}
          />
          <ActivityFeed entries={activity} onRefresh={refreshActivity} />
        </aside>

        <section className="portal-doclist">
          <DocumentList
            client={selectedClient}
            documents={documents}
            loading={documentsLoading}
            selectedIds={selectedIds}
            onSelectOnly={selectOnly}
            onToggleSelected={toggleSelected}
          />
        </section>

        <section className="portal-main">
          <DocumentDetail client={selectedClient} documents={selectedDocuments} onActivity={refreshActivity} />
        </section>
      </div>

      {uploadOpen && <UploadModal onClose={() => setUploadOpen(false)} onSubmit={startUpload} />}
      {pendingUpload && <UploadStatus status={pendingUpload} onDismiss={() => setPendingUpload(null)} />}
    </div>
  )
}
