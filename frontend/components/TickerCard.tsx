"use client";
import Link from 'next/link'
import useSWR from 'swr'
import { fetcher } from '@/lib/api'

export function TickerCard({ symbol }: { symbol: string }) {
  const { data } = useSWR(() => symbol ? `/v1/risk/${symbol}` : null, fetcher)
  const risk = data?.risk?.risk_percent ?? null

  return (
    <Link href={`/ticker/${symbol}`} className="block rounded-lg border bg-white p-4 shadow hover:shadow-md">
      <div className="flex items-baseline justify-between">
        <div>
          <div className="text-sm text-gray-500">Ticker</div>
          <div className="text-xl font-semibold">{symbol}</div>
        </div>
        {risk !== null ? (
          <div className="text-right">
            <div className="text-sm text-gray-500">Risk</div>
            <div className="text-2xl font-bold">{risk}</div>
          </div>
        ) : (
          <div className="text-sm text-gray-400">Loading...</div>
        )}
      </div>
    </Link>
  )
}
