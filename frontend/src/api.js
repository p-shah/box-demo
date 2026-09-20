const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    let message = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (body.error) message = body.error
    } catch {
      // ignore — non-JSON error body
    }
    throw new Error(message)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  listClients: () => request('/clients'),

  listDocuments: (folderId) => request(`/clients/${folderId}/documents`),

  uploadDocument: ({ file, reportType, sensitivity }) => {
    const form = new FormData()
    form.append('file', file)
    form.append('reportType', reportType)
    form.append('sensitivity', sensitivity)
    return request('/documents', { method: 'POST', body: form })
  },

  getSummary: ({ fileIds, fileNames, clientName }) =>
    request('/documents/summary', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fileIds, fileNames, clientName }),
    }),

  getHighlights: ({ fileIds, fileNames, clientName }) =>
    request('/documents/highlights', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fileIds, fileNames, clientName }),
    }),

  createShareLink: (fileId, { fileName, clientName, daysValid }) =>
    request(`/documents/${fileId}/share`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fileName, clientName, daysValid }),
    }),

  documentContentUrl: (fileId, fileName) =>
    `${BASE}/documents/${fileId}/content?fileName=${encodeURIComponent(fileName)}`,

  getActivity: () => request('/activity'),
}
