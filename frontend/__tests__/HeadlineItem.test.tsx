// @ts-nocheck
import { render, screen } from '@testing-library/react'
import { HeadlineItem } from '@/components/HeadlineItem'

describe('HeadlineItem', () => {
  it('renders title and badges', () => {
    render(
      <HeadlineItem item={{ title: 'AAPL plunges after earnings miss', source: 'NewsAPI', sentiment: -0.4, urgency: 0.7 }} />
    )
    expect(screen.getByText('AAPL plunges after earnings miss')).toBeInTheDocument()
    expect(screen.getByText('NewsAPI')).toBeInTheDocument()
    expect(screen.getByText(/Sent/)).toBeInTheDocument()
    expect(screen.getByText(/Urg/)).toBeInTheDocument()
  })
})


