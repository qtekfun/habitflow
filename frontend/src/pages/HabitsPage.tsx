import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useHabits, useCreateHabit, useUpdateHabit, useDeleteHabit } from '@/hooks/useHabits'
import { HabitForm } from '@/components/habits/HabitForm'
import type { Habit } from '@/types'

export function HabitsPage() {
  const { data: habits, isLoading } = useHabits()
  const createHabit = useCreateHabit()
  const updateHabit = useUpdateHabit()
  const deleteHabit = useDeleteHabit()

  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null)

  function handleCreate(values: Partial<Habit>) {
    createHabit.mutate(values as Habit, { onSuccess: () => setShowCreateForm(false) })
  }

  function handleUpdate(id: string, values: Partial<Habit>) {
    updateHabit.mutate({ id, updates: values }, { onSuccess: () => setEditingId(null) })
  }

  function handleDelete(id: string) {
    deleteHabit.mutate(id, { onSuccess: () => setConfirmDeleteId(null) })
  }

  if (isLoading) return <p className="p-4 text-gray-500">Loading habits…</p>

  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Habits</h1>
        <button
          type="button"
          onClick={() => setShowCreateForm(true)}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          New Habit
        </button>
      </div>

      {showCreateForm && (
        <div className="mb-6 rounded-lg border border-gray-200 p-4">
          <h2 className="mb-4 text-lg font-semibold">New Habit</h2>
          <HabitForm
            onSubmit={handleCreate}
            onCancel={() => setShowCreateForm(false)}
            isLoading={createHabit.isPending}
          />
        </div>
      )}

      <div className="space-y-3">
        {habits?.map((habit) => (
          <div key={habit.id} data-testid="habit-card" className="rounded-lg border border-gray-200 p-4">
            {editingId === habit.id ? (
              <HabitForm
                defaultValues={habit}
                onSubmit={(v) => handleUpdate(habit.id, v)}
                onCancel={() => setEditingId(null)}
                isLoading={updateHabit.isPending}
              />
            ) : (
              <div className="flex items-center justify-between">
                <div>
                  <Link
                    to={`/habits/${habit.id}`}
                    className="font-medium text-gray-900 hover:text-indigo-600"
                  >
                    {habit.name}
                  </Link>
                  {habit.description && (
                    <p className="mt-0.5 text-sm text-gray-500">{habit.description}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setEditingId(habit.id)}
                    className="rounded-md bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-200"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmDeleteId(habit.id)}
                    className="rounded-md bg-red-50 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-100"
                  >
                    Delete
                  </button>
                </div>
              </div>
            )}

            {confirmDeleteId === habit.id && (
              <div className="mt-3 rounded-md bg-red-50 p-3">
                <p className="text-sm text-red-700">Are you sure you want to delete <strong>{habit.name}</strong>?</p>
                <div className="mt-2 flex gap-2">
                  <button
                    type="button"
                    onClick={() => handleDelete(habit.id)}
                    className="rounded-md bg-red-600 px-3 py-1 text-xs font-medium text-white"
                  >
                    Confirm
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmDeleteId(null)}
                    className="rounded-md bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </main>
  )
}
