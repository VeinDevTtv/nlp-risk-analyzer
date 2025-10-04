export function HeadlineItem({ item }: { item: any }) {
  const sentimentColor = item.sentiment > 0 ? 'bg-emerald-100 text-emerald-700' : item.sentiment < 0 ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'
  const urgencyColor = item.urgency > 0.66 ? 'bg-orange-100 text-orange-700' : item.urgency > 0.33 ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-700'

  return (
    <div className="flex items-start justify-between rounded-md border p-3">
      <div>
        <div className="font-medium">{item.title}</div>
        {item.source && (
          <div className="text-xs text-gray-500">{item.source}</div>
        )}
      </div>
      <div className="flex gap-2 text-xs">
        <span className={`rounded px-2 py-1 ${sentimentColor}`}>Sent {item.sentiment?.toFixed?.(2)}</span>
        <span className={`rounded px-2 py-1 ${urgencyColor}`}>Urg {Math.round((item.urgency ?? 0) * 100)}%</span>
      </div>
    </div>
  )
}
