import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HabitCard } from '@/components/habits/HabitCard'
import type { TodayStatus } from '@/types'

const mockStatus: TodayStatus = {
  habit_id: 'habit-1',
  name: 'Morning Run',
  completed: false,
  log_id: null,
}

const completedStatus: TodayStatus = {
  habit_id: 'habit-2',
  name: 'Read',
  completed: true,
  log_id: 'log-1',
}

describe('HabitCard', () => {
  it('renders the habit name', () => {
    render(<HabitCard status={mockStatus} streak={3} onCheckIn={vi.fn()} onUndo={vi.fn()} />)
    expect(screen.getByText('Morning Run')).toBeInTheDocument()
  })

  it('shows a check-in button when not completed', () => {
    render(<HabitCard status={mockStatus} streak={0} onCheckIn={vi.fn()} onUndo={vi.fn()} />)
    expect(screen.getByRole('button', { name: /check.?in/i })).toBeInTheDocument()
  })

  it('shows an undo button when completed', () => {
    render(
      <HabitCard status={completedStatus} streak={1} onCheckIn={vi.fn()} onUndo={vi.fn()} />,
    )
    expect(screen.getByRole('button', { name: /undo/i })).toBeInTheDocument()
  })

  it('calls onCheckIn when check-in button is clicked', async () => {
    const onCheckIn = vi.fn()
    render(<HabitCard status={mockStatus} streak={0} onCheckIn={onCheckIn} onUndo={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: /check.?in/i }))
    expect(onCheckIn).toHaveBeenCalledWith('habit-1')
  })

  it('calls onUndo when undo button is clicked', async () => {
    const onUndo = vi.fn()
    render(
      <HabitCard status={completedStatus} streak={1} onCheckIn={vi.fn()} onUndo={onUndo} />,
    )
    await userEvent.click(screen.getByRole('button', { name: /undo/i }))
    expect(onUndo).toHaveBeenCalledWith('log-1')
  })

  it('renders the streak badge when streak > 0', () => {
    render(<HabitCard status={mockStatus} streak={7} onCheckIn={vi.fn()} onUndo={vi.fn()} />)
    expect(screen.getByText('🔥 7 day streak')).toBeInTheDocument()
  })

  it('does not render streak badge when streak is 0', () => {
    render(<HabitCard status={mockStatus} streak={0} onCheckIn={vi.fn()} onUndo={vi.fn()} />)
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})
