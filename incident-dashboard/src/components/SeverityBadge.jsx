const SEVERITY_STYLES = {
  CRITICAL: 'bg-red-600 text-white',
  HIGH: 'bg-orange-500 text-white',
  MEDIUM: 'bg-yellow-400 text-gray-900',
  LOW: 'bg-gray-200 text-gray-700',
}

export default function SeverityBadge({ severity }) {
  const cls = SEVERITY_STYLES[severity] ?? 'bg-gray-200 text-gray-700'
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-bold tracking-wide ${cls}`}>
      {severity}
    </span>
  )
}
