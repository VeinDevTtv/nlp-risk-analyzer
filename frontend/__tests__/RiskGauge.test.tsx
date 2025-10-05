// @ts-nocheck
import { render, screen } from '@testing-library/react'
import { RiskGauge } from '@/components/RiskGauge'

describe('RiskGauge', () => {
  it('renders clamped value and svg', () => {
    render(<RiskGauge value={120} />)
    expect(screen.getAllByText('100').length).toBeGreaterThan(0)
    const svg = screen.queryByRole('img', { hidden: true }) as SVGSVGElement | null
    // If role is not present, ensure an SVG element exists
    expect(svg || document.querySelector('svg')).toBeTruthy()
  })
})


