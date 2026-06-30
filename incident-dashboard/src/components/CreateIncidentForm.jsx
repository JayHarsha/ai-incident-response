import { useState } from 'react'
import { incidentApi } from '../services/api.js'

const SAMPLE_INCIDENTS = [
  { serviceName: 'payment-service', errorMessage: 'HikariCP connection pool exhausted after 30s', severity: 'CRITICAL' },
  { serviceName: 'auth-service', errorMessage: 'OutOfMemoryError: Java heap space', severity: 'HIGH' },
  { serviceName: 'order-service', errorMessage: 'Downstream payment-service unreachable - connection refused', severity: 'HIGH' },
  { serviceName: 'notification-service', errorMessage: 'Kafka consumer lag exceeded threshold - 50000 messages behind', severity: 'MEDIUM' },
  { serviceName: 'inventory-service', errorMessage: 'Database deadlock detected on orders table', severity: 'HIGH' },
]

const SEVERITIES = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']

export default function CreateIncidentForm({ onCreated, onClose }) {
  const [form, setForm] = useState({ serviceName: '', errorMessage: '', severity: 'HIGH', environment: 'PROD' })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const fillSample = (sample) => setForm(f => ({ ...f, ...sample }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.serviceName.trim() || !form.errorMessage.trim()) {
      setError('Service name and error message are required.')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      const { data } = await incidentApi.create(form)
      onCreated(data)
      onClose()
    } catch (err) {
      setError(err.response?.data?.message ?? 'Failed to create incident.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-bold text-gray-900">Report New Incident</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Quick-fill samples */}
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Quick fill from sample</p>
            <div className="flex flex-wrap gap-2">
              {SAMPLE_INCIDENTS.map((s) => (
                <button
                  key={s.serviceName}
                  type="button"
                  onClick={() => fillSample(s)}
                  className="text-xs px-2 py-1 rounded bg-gray-100 hover:bg-blue-100 hover:text-blue-700 text-gray-600 transition-colors"
                >
                  {s.serviceName}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Service Name</label>
            <input
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g. payment-service"
              value={form.serviceName}
              onChange={e => setForm(f => ({ ...f, serviceName: e.target.value }))}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Error Message</label>
            <textarea
              rows={3}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder="Describe the error…"
              value={form.errorMessage}
              onChange={e => setForm(f => ({ ...f, errorMessage: e.target.value }))}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
              <select
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.severity}
                onChange={e => setForm(f => ({ ...f, severity: e.target.value }))}
              >
                {SEVERITIES.map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Environment</label>
              <select
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.environment}
                onChange={e => setForm(f => ({ ...f, environment: e.target.value }))}
              >
                {['PROD', 'STAGING', 'DEV'].map(e => <option key={e}>{e}</option>)}
              </select>
            </div>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900">
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {submitting ? 'Creating…' : 'Create Incident'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
