const API_BASE = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || ''

export async function fetcher(path: string) {
  const res = await fetch(`${API_BASE}${path}`, { next: { revalidate: 30 } })
  if (!res.ok) throw new Error('Network error')
  return res.json()
}

export async function getTickerRisk(symbol: string) {
  if (!symbol) return null
  const res = await fetch(`${API_BASE}/v1/risk/${encodeURIComponent(symbol)}`, { cache: 'no-store' })
  if (!res.ok) {
    return { risk: { risk_percent: 0 }, timeseries: [], headlines: [] }
  }
  const data = await res.json()
  // Normalize expected fields
  return {
    risk: data?.risk ?? { risk_percent: 0 },
    timeseries: data?.timeseries ?? [],
    headlines: data?.headlines ?? [],
  }
}
