const STATUS_STYLES = {
  OPEN: 'bg-red-100 text-red-800 border border-red-200',
  ANALYZING: 'bg-amber-100 text-amber-800 border border-amber-200',
  ANALYZED: 'bg-blue-100 text-blue-800 border border-blue-200',
  RESOLVED: 'bg-green-100 text-green-800 border border-green-200',
}

export default function StatusBadge({ status }) {
  const cls = STATUS_STYLES[status] ?? 'bg-gray-100 text-gray-700 border border-gray-200'
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold ${cls}`}>
      {status === 'ANALYZING' && (
        <span className="inline-block w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
      )}
      {status}
    </span>
  )
}
