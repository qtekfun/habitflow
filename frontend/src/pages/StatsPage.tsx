import { useState } from 'react'
import { useHabits } from '@/hooks/useHabits'
import { useStats } from '@/hooks/useStats'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export function StatsPage() {
  const { data: habits } = useHabits()
  const [selectedId, setSelectedId] = useState<string | undefined>(undefined)
  const { data: stats } = useStats(selectedId ?? '')

  const chartData = stats
    ? [
        { name: 'Completed', value: stats.completed_days },
        { name: 'Missed', value: stats.total_days - stats.completed_days },
      ]
    : []

  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Stats</h1>

      <div className="mb-4">
        <label htmlFor="habit-select" className="block text-sm font-medium text-gray-700">Select habit</label>
        <select
          id="habit-select"
          value={selectedId ?? ''}
          onChange={(e) => setSelectedId(e.target.value || undefined)}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">-- choose a habit --</option>
          {habits?.map((h) => (
            <option key={h.id} value={h.id}>{h.name}</option>
          ))}
        </select>
      </div>

      {stats && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg border border-gray-200 p-4 text-center">
              <p className="text-2xl font-bold text-indigo-600">{Math.round(stats.completion_rate * 100)}%</p>
              <p className="text-sm text-gray-500">Completion rate</p>
            </div>
            <div className="rounded-lg border border-gray-200 p-4 text-center">
              <p className="text-2xl font-bold text-indigo-600">{stats.weekly_average.toFixed(1)}</p>
              <p className="text-sm text-gray-500">Weekly average</p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData}>
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#6366f1" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </main>
  )
}
