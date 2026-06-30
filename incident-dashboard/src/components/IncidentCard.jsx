import { useNavigate } from 'react-router-dom'
import StatusBadge from './StatusBadge.jsx'
import SeverityBadge from './SeverityBadge.jsx'

export default function IncidentCard({ incident }) {
  const navigate = useNavigate()
  const created = new Date(incident.createdAt).toLocaleString()

  return (
    <div
      onClick={() => navigate(`/incidents/${incident.incidentId}`)}
      className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md hover:border-blue-300 transition-all cursor-pointer"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div>
          <span className="font-mono text-sm text-gray-500">{incident.incidentId}</span>
          <h3 className="font-semibold text-gray-900 text-sm mt-0.5">{incident.serviceName}</h3>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <SeverityBadge severity={incident.severity} />
          <StatusBadge status={incident.status} />
        </div>
      </div>
      <p className="text-xs text-gray-600 line-clamp-2">{incident.errorMessage}</p>
      <p className="text-xs text-gray-400 mt-2">{created}</p>
    </div>
  )
}
