import { describe, it, expect, vi, beforeAll } from 'vitest'
import { cn, formatStreak, formatDate, isToday } from '@/lib/utils'

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('px-4', 'py-2')).toBe('px-4 py-2')
  })

  it('handles conditional classes', () => {
    expect(cn('base', false && 'skip', 'include')).toBe('base include')
  })

  it('deduplicates conflicting tailwind classes', () => {
    // tailwind-merge keeps the last one
    expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500')
  })

  it('handles undefined and null values', () => {
    expect(cn('base', undefined, null, 'end')).toBe('base end')
  })
})

describe('formatStreak', () => {
  it('returns empty string for 0', () => {
    expect(formatStreak(0)).toBe('')
  })

  it('returns singular for 1', () => {
    expect(formatStreak(1)).toBe('🔥 1 day streak')
  })

  it('returns plural for more than 1', () => {
    expect(formatStreak(5)).toBe('🔥 5 day streak')
  })

  it('returns plural for 2', () => {
    expect(formatStreak(2)).toBe('🔥 2 day streak')
  })
})

describe('formatDate', () => {
  it('formats an ISO date string as "Mon, Apr 7"', () => {
    expect(formatDate('2026-04-07')).toBe('Tue, Apr 7')
  })

  it('formats another date correctly', () => {
    expect(formatDate('2026-01-01')).toBe('Thu, Jan 1')
  })

  it('formats another date correctly', () => {
    expect(formatDate('2026-12-25')).toBe('Fri, Dec 25')
  })
})

describe('isToday', () => {
  beforeAll(() => {
    // Fix "today" to 2026-04-09 for deterministic tests
    vi.setSystemTime(new Date('2026-04-09T12:00:00Z'))
  })

  it('returns true for today', () => {
    expect(isToday('2026-04-09')).toBe(true)
  })

  it('returns false for yesterday', () => {
    expect(isToday('2026-04-08')).toBe(false)
  })

  it('returns false for a future date', () => {
    expect(isToday('2026-04-10')).toBe(false)
  })
})
