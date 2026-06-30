import { useState } from 'react'
import StatusBadge from './StatusBadge.jsx'
import SeverityBadge from './SeverityBadge.jsx'
import { incidentApi } from '../services/api.js'

export default function IncidentDetail({ incident, onUpdated }) {
  const [updating, setUpdating] = useState(false)

  const handleStatusUpdate = async (newStatus) => {
    setUpdating(true)
    try {
      const { data } = await incidentApi.updateStatus(incident.incidentId, newStatus)
      onUpdated(data)
    } finally {
      setUpdating(false)
    }
  }

  const hasAnalysis = incident.rootCauseHypothesis || incident.remediationSteps

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-sm text-gray-500">{incident.incidentId}</span>
              <span className="text-gray-300">·</span>
              <span className="text-xs text-gray-500">{incident.traceId}</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">{incident.serviceName}</h1>
            <p className="text-sm text-gray-500 mt-1">{incident.environment} · Reported {new Date(incident.createdAt).toLocaleString()}</p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <SeverityBadge severity={incident.severity} />
            <StatusBadge status={incident.status} />
          </div>
        </div>

        <div className="mt-4 p-3 bg-red-50 border border-red-100 rounded-lg">
          <p className="text-sm font-mono text-red-800">{incident.errorMessage}</p>
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap gap-2 mt-4">
          {incident.status !== 'RESOLVED' && (
            <button
              onClick={() => handleStatusUpdate('RESOLVED')}
              disabled={updating}
              className="px-4 py-2 bg-green-600 text-white text-sm font-semibold rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {updating ? 'Updating…' : 'Mark Resolved'}
            </button>
          )}
          {incident.status === 'OPEN' && (
            <button
              onClick={() => handleStatusUpdate('ANALYZING')}
              disabled={updating}
              className="px-4 py-2 bg-amber-500 text-white text-sm font-semibold rounded-lg hover:bg-amber-600 disabled:opacity-50 transition-colors"
            >
              Start Analysis
            </button>
          )}
        </div>
      </div>

      {/* AI Analysis */}
      {hasAnalysis ? (
        <div className="bg-white rounded-xl border border-blue-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-blue-600 text-lg">🤖</span>
            <h2 className="text-lg font-bold text-gray-900">AI Analysis Report</h2>
            {incident.aiConfidenceScore != null && (
              <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 font-semibold border border-blue-200">
                Confidence: {Math.round(incident.aiConfidenceScore * 100)}%
              </span>
            )}
          </div>

          {incident.rootCauseHypothesis && (
            <Section title="Root Cause Hypothesis">
              <p className="text-sm text-gray-700">{incident.rootCauseHypothesis}</p>
              <p className="text-xs text-amber-600 mt-1">⚠ AI-generated hypothesis — verify against live logs before acting.</p>
            </Section>
          )}

          {incident.remediationSteps && (
            <Section title="Remediation Steps">
              <ul className="space-y-1">
                {incident.remediationSteps.split('\n').filter(Boolean).map((step, i) => (
                  <li key={i} className="text-sm text-gray-700 flex gap-2">
                    <span className="text-blue-500 shrink-0">›</span>
                    {step.replace(/^[•\-]\s*/, '')}
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {incident.impactedServices && (
            <Section title="Impacted Services">
              <ul className="flex flex-wrap gap-2">
                {incident.impactedServices.split('\n').filter(Boolean).map((svc, i) => (
                  <li key={i} className="text-xs px-2 py-1 rounded-full bg-red-50 text-red-700 border border-red-100 font-medium">
                    {svc.replace(/^[•\-]\s*/, '')}
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {incident.similarPastIncidents && (
            <Section title="Similar Past Incidents">
              <ul className="space-y-1">
                {incident.similarPastIncidents.split('\n').filter(Boolean).map((inc, i) => (
                  <li key={i} className="text-sm text-gray-600 flex gap-2">
                    <span className="text-gray-400 shrink-0">›</span>
                    {inc.replace(/^[•\-]\s*/, '')}
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {incident.matchedRunbook && (
            <Section title="Matched Runbook">
              <p className="text-sm text-gray-700 font-medium">
                {incident.matchedRunbook.replace(/^#+\s*/, '')}
              </p>
            </Section>
          )}

          {incident.aiAnalysisTimestamp && (
            <p className="text-xs text-gray-400 mt-4">
              Analysed at {new Date(incident.aiAnalysisTimestamp).toLocaleString()}
            </p>
          )}
        </div>
      ) : (
        incident.status === 'ANALYZING' ? (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 text-center">
            <div className="inline-block w-8 h-8 border-4 border-amber-400 border-t-transparent rounded-full animate-spin mb-3" />
            <p className="text-amber-800 font-semibold">AI agent is investigating this incident…</p>
            <p className="text-amber-600 text-sm mt-1">This page refreshes automatically every 10 seconds.</p>
          </div>
        ) : (
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 text-center text-gray-400">
            <p>No AI analysis available yet.</p>
          </div>
        )
      )}
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div className="mb-4">
      <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-2">{title}</h3>
      {children}
    </div>
  )
}
