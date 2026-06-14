const API_BASE = import.meta.env.VITE_API_BASE || '/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  })

  const data = await response.json()
  if (!response.ok || data.error) {
    throw new Error(data.error || '请求失败')
  }
  return data
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) }),
  put: (path, body) => request(path, { method: 'PUT', body: JSON.stringify(body) }),
  delete: (path) => request(path, { method: 'DELETE' })
}

export function createCRUDApi(endpoint) {
  return {
    list: (params) => {
      const query = params ? '?' + new URLSearchParams(params).toString() : ''
      return api.get(`${endpoint}/${query}`)
    },
    create: (payload) => api.post(`${endpoint}/`, payload),
    update: (id, payload) => api.put(`${endpoint}/${id}/`, payload),
    remove: (id) => api.delete(`${endpoint}/${id}/`)
  }
}

export const residentsApi = createCRUDApi('/residents')
export const appointmentsApi = createCRUDApi('/appointments')
export const visitsApi = createCRUDApi('/visits')
export const notificationsApi = createCRUDApi('/notifications')
