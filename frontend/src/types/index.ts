export interface User {
  id: string
  email: string
  username: string
  timezone: string
  totp_enabled: boolean
  is_active: boolean
}

export interface Habit {
  id: string
  user_id: string
  name: string
  description: string | null
  color: string
  icon: string
  frequency: 'daily' | 'weekly'
  target_days: number[]
  notify_time: string | null
  is_active: boolean
  sort_order: number
  current_streak?: number
  longest_streak?: number
}

export interface HabitLog {
  id: string
  habit_id: string
  user_id: string
  log_date: string
  completed: boolean
  note: string | null
}

export interface TodayStatus {
  habit_id: string
  name: string
  completed: boolean
  log_id: string | null
}

export interface StatsResponse {
  total_days: number
  completed_days: number
  completion_rate: number
  weekly_average: number
}
