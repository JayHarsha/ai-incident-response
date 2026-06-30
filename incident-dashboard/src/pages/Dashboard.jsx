import { useState, useEffect, useCallback } from 'react'
import IncidentList from '../components/IncidentList.jsx'
import CreateIncidentForm from '../components/CreateIncidentForm.jsx'
import { incidentApi } from '../services/api.js'

const AUTO_REFRESH_MS = 10_000

const SUMMARY_STATUSES = ['OPEN', 'ANALYZING', 'ANALYZED', 'RESOLVED']

export default function Dashboard() {
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [filter, setFilter] = useState('ALL')
  const [lastRefresh, setLastRefresh] = useState(null)

  const fetchIncidents = useCallback(async () => {
    try {
      const { data } = await incidentApi.getAll()
      setIncidents(data)
      setLastRefresh(new Date())
    } catch (err) {
      console.error('Failed to fetch incidents:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchIncidents()
    const interval = setInterval(fetchIncidents, AUTO_REFRESH_MS)
    return () => clearInterval(interval)
  }, [fetchIncidents])

  const counts = SUMMARY_STATUSES.reduce((acc, s) => {
    acc[s] = incidents.filter(i => i.status === s).length
    return acc
  }, {})

  const displayed = filter === 'ALL' ? incidents : incidents.filter(i => i.status === filter)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🛡️</span>
            <div>
              <h1 className="text-base font-bold text-gray-900 leading-tight">Incident Resolution Platform</h1>
              <p className="text-xs text-gray-500">Agentic AI · Real-time</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {lastRefresh && (
              <span className="text-xs text-gray-400 hidden sm:block">
                Updated {lastRefresh.toLocaleTimeString()}
              </span>
            )}
            <button
              onClick={fetchIncidents}
              className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Refresh
            </button>
            <button
              onClick={() => setShowForm(true)}
              className="text-sm px-4 py-1.5 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            >
              + Report Incident
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Summary cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[
            { label: 'Open', status: 'OPEN', color: 'text-red-600', bg: 'bg-red-50 border-red-100' },
            { label: 'Analyzing', status: 'ANALYZING', color: 'text-amber-600', bg: 'bg-amber-50 border-amber-100' },
            { label: 'Analyzed', status: 'ANALYZED', color: 'text-blue-600', bg: 'bg-blue-50 border-blue-100' },
            { label: 'Resolved', status: 'RESOLVED', color: 'text-green-600', bg: 'bg-green-50 border-green-100' },
          ].map(({ label, status, color, bg }) => (
            <button
              key={status}
              onClick={() => setFilter(filter === status ? 'ALL' : status)}
              className={`rounded-xl border p-4 text-left transition-all ${bg} ${filter === status ? 'ring-2 ring-offset-1 ring-blue-400' : 'hover:shadow-sm'}`}
            >
              <p className={`text-2xl font-bold ${color}`}>{counts[status] ?? 0}</p>
              <p className="text-xs font-medium text-gray-500 mt-0.5">{label}</p>
            </button>
          ))}
        </div>

        {/* Filter bar */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-gray-700">
            {filter === 'ALL' ? `All Incidents (${incidents.length})` : `${filter} (${displayed.length})`}
          </h2>
          {filter !== 'ALL' && (
            <button onClick={() => setFilter('ALL')} className="text-xs text-blue-600 hover:underline">
              Clear filter
            </button>
          )}
        </div>

        <IncidentList incidents={displayed} loading={loading} />
      </main>

      {showForm && (
        <CreateIncidentForm
          onCreated={(newInc) => setIncidents(prev => [newInc, ...prev])}
          onClose={() => setShowForm(false)}
        />
      )}
    </div>
  )
}
