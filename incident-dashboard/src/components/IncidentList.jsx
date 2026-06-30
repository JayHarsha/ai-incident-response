import IncidentCard from './IncidentCard.jsx'

const STATUS_ORDER = { OPEN: 0, ANALYZING: 1, ANALYZED: 2, RESOLVED: 3 }

export default function IncidentList({ incidents, loading }) {
  if (loading) {
    return (
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="bg-gray-100 rounded-lg h-28 animate-pulse" />
        ))}
      </div>
    )
  }

  if (!incidents.length) {
    return (
      <div className="text-center py-20 text-gray-400">
        <p className="text-4xl mb-3">🎉</p>
        <p className="font-medium">No incidents — all systems healthy!</p>
      </div>
    )
  }

  const sorted = [...incidents].sort((a, b) => STATUS_ORDER[a.status] - STATUS_ORDER[b.status])

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {sorted.map(inc => <IncidentCard key={inc.incidentId} incident={inc} />)}
    </div>
  )
}
