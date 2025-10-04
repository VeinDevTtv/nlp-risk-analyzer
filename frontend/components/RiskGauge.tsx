type Props = { value: number }

export function RiskGauge({ value }: Props) {
  const clamped = Math.max(0, Math.min(100, Number(value) || 0))
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const progress = (clamped / 100) * circumference
  const remaining = circumference - progress

  const color = clamped > 66 ? '#ef4444' : clamped > 33 ? '#f59e0b' : '#10b981'

  return (
    <div className="flex items-center gap-4">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={radius} stroke="#e5e7eb" strokeWidth="12" fill="none" />
        <circle
          cx="70"
          cy="70"
          r={radius}
          stroke={color}
          strokeWidth="12"
          fill="none"
          strokeDasharray={`${progress} ${remaining}`}
          transform="rotate(-90 70 70)"
          strokeLinecap="round"
        />
        <text x="70" y="78" textAnchor="middle" fontSize="22" fontWeight="700" fill="#111827">
          {clamped}
        </text>
      </svg>
      <div>
        <div className="text-sm text-gray-500">Composite Risk</div>
        <div className="text-2xl font-semibold">{clamped}</div>
      </div>
    </div>
  )
}
