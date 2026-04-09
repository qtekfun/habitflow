import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import type { Habit } from '@/types'

const habitSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  description: z.string().optional(),
  color: z.string().regex(/^#[0-9a-fA-F]{6}$/),
  icon: z.string(),
  frequency: z.enum(['daily', 'weekly']),
  notify_time: z.string().nullable().optional(),
})

type HabitFormValues = z.infer<typeof habitSchema>

interface HabitFormProps {
  defaultValues?: Partial<Habit>
  onSubmit: (values: HabitFormValues) => void
  onCancel: () => void
  isLoading?: boolean
}

export function HabitForm({ defaultValues, onSubmit, onCancel, isLoading }: HabitFormProps) {
  const { register, handleSubmit, formState: { errors } } = useForm<HabitFormValues>({
    resolver: zodResolver(habitSchema),
    defaultValues: {
      name: defaultValues?.name ?? '',
      description: defaultValues?.description ?? '',
      color: defaultValues?.color ?? '#6366f1',
      icon: defaultValues?.icon ?? 'check',
      frequency: defaultValues?.frequency ?? 'daily',
      notify_time: defaultValues?.notify_time ?? null,
    },
  })

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700">Name</label>
        <input
          id="name"
          {...register('name')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        {errors.name && <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>}
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700">Description</label>
        <textarea
          id="description"
          {...register('description')}
          rows={2}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div>
        <label htmlFor="frequency" className="block text-sm font-medium text-gray-700">Frequency</label>
        <select
          id="frequency"
          {...register('frequency')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
        </select>
      </div>

      <div>
        <label htmlFor="color" className="block text-sm font-medium text-gray-700">Color</label>
        <input
          id="color"
          type="color"
          {...register('color')}
          className="mt-1 h-9 w-16 cursor-pointer rounded-md border border-gray-300"
        />
      </div>

      <div>
        <label htmlFor="notify_time" className="block text-sm font-medium text-gray-700">Notify at (optional)</label>
        <input
          id="notify_time"
          type="time"
          {...register('notify_time')}
          className="mt-1 block rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={isLoading}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          Save
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}
