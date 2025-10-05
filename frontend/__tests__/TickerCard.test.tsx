// @ts-nocheck
import { render, screen } from '@testing-library/react'
import { TickerCard } from '@/components/TickerCard'

jest.mock('swr', () => ({
  __esModule: true,
  default: (key: any) => ({ data: key ? { risk: { risk_percent: 42 } } : undefined }),
}))

describe('TickerCard', () => {
  it('shows symbol and risk when loaded', () => {
    render(<TickerCard symbol="AAPL" />)
    expect(screen.getByText('AAPL')).toBeInTheDocument()
    expect(screen.getByText('Risk')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
  })
})


