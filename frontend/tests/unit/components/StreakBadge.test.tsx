import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StreakBadge } from '@/components/habits/StreakBadge'

describe('StreakBadge', () => {
  it('renders nothing when streak is 0', () => {
    const { container } = render(<StreakBadge streak={0} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders the streak text for streak = 1', () => {
    render(<StreakBadge streak={1} />)
    expect(screen.getByText('🔥 1 day streak')).toBeInTheDocument()
  })

  it('renders the streak text for streak = 5', () => {
    render(<StreakBadge streak={5} />)
    expect(screen.getByText('🔥 5 day streak')).toBeInTheDocument()
  })

  it('applies the correct role for accessibility', () => {
    render(<StreakBadge streak={3} />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})
