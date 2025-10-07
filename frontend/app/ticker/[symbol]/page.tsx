import { RiskGauge } from '@/components/RiskGauge'
import { TimeseriesChart } from '@/components/TimeseriesChart'
import { HeadlineItem } from '@/components/HeadlineItem'
import { Header } from '@/components/Header'
import { Footer } from '@/components/Footer'
import { getTickerRisk } from '@/lib/api'

export const revalidate = 60

export default async function TickerPage({ params }: { params: { symbol: string } }) {
  const { symbol } = params
  const data = await getTickerRisk(symbol)
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <div className="container-page py-8">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-semibold">{symbol.toUpperCase()} Risk Overview</h1>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="rounded-lg bg-white p-6 shadow lg:col-span-1">
            <h2 className="mb-4 text-lg font-medium">Risk Gauge</h2>
            <RiskGauge value={data?.risk?.risk_percent ?? 0} />
          </div>
          <div className="rounded-lg bg-white p-6 shadow lg:col-span-2">
            <h2 className="mb-4 text-lg font-medium">Risk Over Time</h2>
            <TimeseriesChart data={data?.timeseries ?? []} />
          </div>
        </div>

        <div className="mt-6 rounded-lg bg-white p-6 shadow">
          <h2 className="mb-4 text-lg font-medium">Recent Headlines</h2>
          <div className="space-y-3">
            {(data?.headlines ?? []).map((h: any) => (
              <HeadlineItem key={h.id} item={h} />
            ))}
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}
