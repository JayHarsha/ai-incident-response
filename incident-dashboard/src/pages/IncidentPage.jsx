import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import IncidentDetail from '../components/IncidentDetail.jsx'
import { incidentApi } from '../services/api.js'

const AUTO_REFRESH_MS = 10_000
const DONE_STATUSES = new Set(['ANALYZED', 'RESOLVED'])

// ─── LangGraph node config ────────────────────────────────────────────────────

const NODES = [
  { key: 'classify',          label: 'Classify Incident',       parallel: false },
  { key: 'rag_search',        label: 'Search Knowledge Base',   parallel: true  },
  { key: 'gather_context',    label: 'Gather Live Context',     parallel: true  },
  { key: 'generate_analysis', label: 'Generate Analysis',       parallel: false },
  { key: 'publish',           label: 'Publish Results',         parallel: false },
]

// ─── Progress tracker component ───────────────────────────────────────────────

function NodeProgressTracker({ completedNodes }) {
  // Split NODES into rows: sequential → own row, parallel pair → one shared row
  const rows = []
  let i = 0
  while (i < NODES.length) {
    if (NODES[i].parallel) {
      const parallelGroup = []
      while (i < NODES.length && NODES[i].parallel) {
        parallelGroup.push(NODES[i])
        i++
      }
      rows.push({ type: 'parallel', nodes: parallelGroup })
    } else {
      rows.push({ type: 'single', nodes: [NODES[i]] })
      i++
    }
  }

  const nodeStatus = (key) => {
    if (completedNodes.has(key)) return 'done'
    return 'pending'
  }

  const NodeChip = ({ node }) => {
    const status = nodeStatus(node.key)
    return (
      <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium transition-all duration-500
        ${status === 'done'
          ? 'bg-emerald-50 border-emerald-300 text-emerald-700'
          : 'bg-gray-50 border-gray-200 text-gray-400'}`}
      >
        <span className="text-base">
          {status === 'done' ? '✓' : '○'}
        </span>
        <span>{node.label}</span>
      </div>
    )
  }

  return (
    <div className="bg-white border border-blue-100 rounded-xl p-4 mb-5 shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
        <span className="text-sm font-semibold text-blue-700">AI Agent Running — LangGraph Progress</span>
      </div>

      <div className="flex flex-col gap-2">
        {rows.map((row, ri) => (
          <div key={ri}>
            {row.type === 'single' ? (
              <NodeChip node={row.nodes[0]} />
            ) : (
              <div>
                <div className="text-xs text-gray-400 pl-1 mb-1">↳ parallel branches</div>
                <div className="flex gap-2 flex-wrap">
                  {row.nodes.map((n) => <NodeChip key={n.key} node={n} />)}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <p className="text-xs text-gray-400 mt-3">
        {completedNodes.size}/{NODES.length} nodes completed
      </p>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function IncidentPage() {
  const { incidentId } = useParams()
  const navigate = useNavigate()
  const [incident, setIncident] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [completedNodes, setCompletedNodes] = useState(new Set())
  const wsRef = useRef(null)

  const fetchIncident = useCallback(async () => {
    try {
      const { data } = await incidentApi.getById(incidentId)
      setIncident(data)
    } catch {
      setError('Incident not found.')
    } finally {
      setLoading(false)
    }
  }, [incidentId])

  useEffect(() => {
    fetchIncident()
  }, [fetchIncident])

  // Auto-refresh only while the incident is still in-progress
  useEffect(() => {
    if (!incident || DONE_STATUSES.has(incident.status)) return
    const interval = setInterval(fetchIncident, AUTO_REFRESH_MS)
    return () => clearInterval(interval)
  }, [incident, fetchIncident])

  // WebSocket: connect while ANALYZING, disconnect when done
  useEffect(() => {
    if (!incident) return

    if (incident.status === 'ANALYZING') {
      if (wsRef.current) return   // already connected
      const ws = new WebSocket(`ws://localhost:3000/ws/incidents/${incidentId}`)

      ws.onopen = () => console.info('[WS] connected for', incidentId)

      ws.onmessage = (e) => {
        try {
          const { node } = JSON.parse(e.data)
          if (node) {
            setCompletedNodes((prev) => {
              const next = new Set(prev)
              next.add(node)
              return next
            })
          }
        } catch {/* ignore malformed frames */}
      }

      ws.onclose = () => {
        console.info('[WS] closed for', incidentId)
        wsRef.current = null
      }

      wsRef.current = ws
    } else if (DONE_STATUSES.has(incident.status) && wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [incident?.status, incidentId])

  const showProgress = incident?.status === 'ANALYZING'

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="text-sm text-gray-500 hover:text-gray-800 flex items-center gap-1"
          >
            ← Back
          </button>
          <span className="text-gray-300">|</span>
          <span className="text-sm font-semibold text-gray-700">Incident Detail</span>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6">
        {loading && (
          <div className="space-y-4">
            <div className="h-40 bg-gray-200 rounded-xl animate-pulse" />
            <div className="h-60 bg-gray-200 rounded-xl animate-pulse" />
          </div>
        )}
        {error && (
          <div className="text-center py-20 text-red-500">
            <p className="text-lg font-semibold">{error}</p>
            <button onClick={() => navigate('/')} className="mt-4 text-blue-600 hover:underline text-sm">
              Back to Dashboard
            </button>
          </div>
        )}
        {incident && (
          <>
            {showProgress && <NodeProgressTracker completedNodes={completedNodes} />}
            <IncidentDetail
              incident={incident}
              onUpdated={(updated) => setIncident(updated)}
            />
          </>
        )}
      </main>
    </div>
  )
}
