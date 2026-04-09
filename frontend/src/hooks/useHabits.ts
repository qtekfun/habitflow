import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { Habit } from '@/types'

const HABITS_KEY = ['habits'] as const

export function useHabits() {
  return useQuery({
    queryKey: HABITS_KEY,
    queryFn: async () => {
      const { data } = await api.get<Habit[]>('/api/v1/habits')
      return data
    },
  })
}

export function useHabit(id: string) {
  return useQuery({
    queryKey: [...HABITS_KEY, id],
    queryFn: async () => {
      const { data } = await api.get<Habit>(`/api/v1/habits/${id}`)
      return data
    },
    enabled: !!id,
  })
}

export function useCreateHabit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: Habit) => {
      const { data } = await api.post<Habit>('/api/v1/habits', payload)
      return data
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: HABITS_KEY }),
  })
}

export function useUpdateHabit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, updates }: { id: string; updates: Partial<Habit> }) => {
      const { data } = await api.patch<Habit>(`/api/v1/habits/${id}`, updates)
      return data
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: HABITS_KEY }),
  })
}

export function useDeleteHabit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/habits/${id}`)
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: HABITS_KEY }),
  })
}
