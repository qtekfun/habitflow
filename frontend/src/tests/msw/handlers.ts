import { http, HttpResponse } from 'msw'
import type { Habit } from '@/types'

export const mockHabits: Habit[] = [
  {
    id: 'habit-1',
    user_id: 'user-1',
    name: 'Morning Run',
    description: 'Run 5km every morning',
    color: '#6366f1',
    icon: 'run',
    frequency: 'daily',
    target_days: [1, 2, 3, 4, 5, 6, 7],
    notify_time: '07:00',
    is_active: true,
    sort_order: 0,
    current_streak: 3,
    longest_streak: 10,
  },
  {
    id: 'habit-2',
    user_id: 'user-1',
    name: 'Read',
    description: null,
    color: '#10b981',
    icon: 'book',
    frequency: 'daily',
    target_days: [1, 2, 3, 4, 5, 6, 7],
    notify_time: null,
    is_active: true,
    sort_order: 1,
    current_streak: 0,
    longest_streak: 5,
  },
]

export const handlers = [
  http.get('/api/v1/habits', () => HttpResponse.json(mockHabits)),

  http.get('/api/v1/habits/:id', ({ params }) => {
    const habit = mockHabits.find((h) => h.id === params['id'])
    if (!habit) return new HttpResponse(null, { status: 404 })
    return HttpResponse.json(habit)
  }),

  http.post('/api/v1/habits', async ({ request }) => {
    const body = (await request.json()) as Partial<Habit>
    const newHabit: Habit = {
      id: 'habit-new',
      user_id: 'user-1',
      name: body.name ?? '',
      description: body.description ?? null,
      color: body.color ?? '#6366f1',
      icon: body.icon ?? 'check',
      frequency: body.frequency ?? 'daily',
      target_days: body.target_days ?? [1, 2, 3, 4, 5, 6, 7],
      notify_time: body.notify_time ?? null,
      is_active: true,
      sort_order: 2,
      current_streak: 0,
      longest_streak: 0,
    }
    return HttpResponse.json(newHabit, { status: 201 })
  }),

  http.patch('/api/v1/habits/:id', async ({ params, request }) => {
    const habit = mockHabits.find((h) => h.id === params['id'])
    if (!habit) return new HttpResponse(null, { status: 404 })
    const body = (await request.json()) as Partial<Habit>
    return HttpResponse.json({ ...habit, ...body })
  }),

  http.delete('/api/v1/habits/:id', ({ params }) => {
    const habit = mockHabits.find((h) => h.id === params['id'])
    if (!habit) return new HttpResponse(null, { status: 404 })
    return new HttpResponse(null, { status: 204 })
  }),
]
