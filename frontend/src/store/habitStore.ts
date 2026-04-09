import { create } from 'zustand'
import type { Habit } from '@/types'

interface HabitState {
  habits: Habit[]
  setHabits: (habits: Habit[]) => void
}

export const useHabitStore = create<HabitState>()((set) => ({
  habits: [],
  setHabits: (habits) => set({ habits }),
}))
