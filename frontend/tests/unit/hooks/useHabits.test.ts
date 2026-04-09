import { describe, it, expect, beforeAll, afterEach, afterAll } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { server } from '@/tests/msw/server'
import { mockHabits } from '@/tests/msw/handlers'
import { useHabits, useHabit, useCreateHabit, useUpdateHabit, useDeleteHabit } from '@/hooks/useHabits'
import type { Habit } from '@/types'

// Start/stop MSW
beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

function wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return React.createElement(QueryClientProvider, { client: queryClient }, children)
}

describe('useHabits', () => {
  it('fetches and returns the list of habits', async () => {
    const { result } = renderHook(() => useHabits(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(mockHabits)
  })
})

describe('useHabit', () => {
  it('fetches a single habit by id', async () => {
    const { result } = renderHook(() => useHabit('habit-1'), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.id).toBe('habit-1')
    expect(result.current.data?.name).toBe('Morning Run')
  })

  it('returns an error for a non-existent habit', async () => {
    const { result } = renderHook(() => useHabit('no-such-id'), { wrapper })
    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useCreateHabit', () => {
  it('creates a new habit and returns it', async () => {
    const { result } = renderHook(() => useCreateHabit(), { wrapper })
    const payload: Partial<Habit> = { name: 'Meditate', frequency: 'daily' }
    result.current.mutate(payload as Habit)
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.name).toBe('Meditate')
  })
})

describe('useUpdateHabit', () => {
  it('updates an existing habit', async () => {
    const { result } = renderHook(() => useUpdateHabit(), { wrapper })
    result.current.mutate({ id: 'habit-1', updates: { name: 'Evening Run' } })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.name).toBe('Evening Run')
  })
})

describe('useDeleteHabit', () => {
  it('deletes a habit without error', async () => {
    const { result } = renderHook(() => useDeleteHabit(), { wrapper })
    result.current.mutate('habit-1')
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
  })
})
