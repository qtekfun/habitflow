import { HabitCard } from '@/components/habits/HabitCard'
import { useTodayStatus, useCheckIn, useUndoCheckIn } from '@/hooks/useLogs'
import { useHabits } from '@/hooks/useHabits'

export function Dashboard() {
  const { data: todayStatus, isLoading } = useTodayStatus()
  const { data: habits } = useHabits()
  const checkIn = useCheckIn()
  const undoCheckIn = useUndoCheckIn()

  function getStreak(habitId: string) {
    return habits?.find((h) => h.id === habitId)?.current_streak ?? 0
  }

  if (isLoading) {
    return <p className="p-4 text-gray-500">Loading today's habits…</p>
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Dashboard</h1>
      {!todayStatus?.length ? (
        <p className="text-gray-500">No habits yet. <a href="/habits" className="text-indigo-600 hover:underline">Create one!</a></p>
      ) : (
        <div className="space-y-3">
          {todayStatus.map((status) => (
            <HabitCard
              key={status.habit_id}
              status={status}
              streak={getStreak(status.habit_id)}
              onCheckIn={(id) => checkIn.mutate(id)}
              onUndo={(logId) => undoCheckIn.mutate(logId)}
            />
          ))}
        </div>
      )}

      <p className="mt-6 text-center text-sm text-gray-500">
        Welcome to HabitFlow
      </p>
    </main>
  )
}
