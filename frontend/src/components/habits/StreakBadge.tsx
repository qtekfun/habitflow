import { formatStreak } from '@/lib/utils'

interface StreakBadgeProps {
  streak: number
}

export function StreakBadge({ streak }: StreakBadgeProps) {
  const label = formatStreak(streak)
  if (!label) return null
  return (
    <span
      role="status"
      className="inline-flex items-center rounded-full bg-orange-100 px-2.5 py-0.5 text-xs font-medium text-orange-800"
    >
      {label}
    </span>
  )
}
