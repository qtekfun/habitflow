import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { HabitLog, TodayStatus, StatsResponse } from '@/types'

const LOGS_KEY = ['logs'] as const
const TODAY_KEY = ['logs', 'today'] as const

export function useTodayStatus() {
  return useQuery({
    queryKey: TODAY_KEY,
    queryFn: async () => {
      const { data } = await api.get<TodayStatus[]>('/api/v1/logs/today')
      return data
    },
  })
}

export function useLogs(habitId?: string) {
  return useQuery({
    queryKey: [...LOGS_KEY, habitId],
    queryFn: async () => {
      const params = habitId ? `?habit_id=${habitId}` : ''
      const { data } = await api.get<HabitLog[]>(`/api/v1/logs${params}`)
      return data
    },
  })
}

export function useStats(habitId: string) {
  return useQuery({
    queryKey: ['logs', 'stats', habitId],
    queryFn: async () => {
      const { data } = await api.get<StatsResponse>(`/api/v1/logs/stats?habit_id=${habitId}`)
      return data
    },
    enabled: !!habitId,
  })
}

export function useCheckIn() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (habitId: string) => {
      const { data } = await api.post<HabitLog>('/api/v1/logs', { habit_id: habitId })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: LOGS_KEY })
      queryClient.invalidateQueries({ queryKey: TODAY_KEY })
    },
  })
}

export function useUndoCheckIn() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (logId: string) => {
      await api.delete(`/api/v1/logs/${logId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: LOGS_KEY })
      queryClient.invalidateQueries({ queryKey: TODAY_KEY })
    },
  })
}
