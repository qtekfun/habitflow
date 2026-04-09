import { cn } from '@/lib/utils'
import { StreakBadge } from './StreakBadge'
import type { TodayStatus } from '@/types'

interface HabitCardProps {
  status: TodayStatus
  streak: number
  onCheckIn: (habitId: string) => void
  onUndo: (logId: string) => void
}

export function HabitCard({ status, streak, onCheckIn, onUndo }: HabitCardProps) {
  return (
    <div
      className={cn(
        'flex items-center justify-between rounded-lg border p-4',
        status.completed ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-white',
      )}
    >
      <div className="flex flex-col gap-1">
        <span className="font-medium text-gray-900">{status.name}</span>
        <StreakBadge streak={streak} />
      </div>

      {status.completed ? (
        <button
          type="button"
          onClick={() => onUndo(status.log_id!)}
          className="rounded-md bg-gray-100 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-200"
        >
          Undo
        </button>
      ) : (
        <button
          type="button"
          onClick={() => onCheckIn(status.habit_id)}
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Check In
        </button>
      )}
    </div>
  )
}
