const PUBLIC_API_BASE = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || ''
const INTERNAL_API_BASE = process.env.API_URL_INTERNAL?.replace(/\/$/, '') || ''

function getApiBase() {
  // On the server within Docker, prefer internal base to avoid localhost resolution issues
  if (typeof window === 'undefined' && INTERNAL_API_BASE) return INTERNAL_API_BASE
  return PUBLIC_API_BASE
}

export async function fetcher(path: string) {
  const base = getApiBase()
  const res = await fetch(`${base}${path}`, { next: { revalidate: 30 } })
  if (!res.ok) throw new Error('Network error')
  return res.json()
}

export async function getTickerRisk(symbol: string) {
  if (!symbol) return null
  const base = getApiBase()
  const res = await fetch(`${base}/v1/risk/${encodeURIComponent(symbol)}`, { cache: 'no-store' })
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
