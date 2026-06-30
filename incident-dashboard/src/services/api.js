import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

export const incidentApi = {
  getAll: () => api.get('/incidents'),
  getById: (id) => api.get(`/incidents/${id}`),
  create: (data) => api.post('/incidents', data),
  updateStatus: (id, status, resolvedBy) =>
    api.put(`/incidents/${id}/status`, { status, resolvedBy }),
  getByService: (name) => api.get(`/incidents/service/${name}`),
}
