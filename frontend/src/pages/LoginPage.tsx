import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import type { User } from '@/types'

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
})
type FormValues = z.infer<typeof schema>

export function LoginPage() {
  const navigate = useNavigate()
  const { setUser, setAccessToken } = useAuthStore()
  const [error, setError] = useState<string | null>(null)
  const [totpRequired, setTotpRequired] = useState(false)
  const [tempToken, setTempToken] = useState<string | null>(null)
  const [totpCode, setTotpCode] = useState('')

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })

  async function onSubmit(values: FormValues) {
    setError(null)
    try {
      const { data } = await api.post<
        { access_token: string; user: User } | { totp_required: true; temp_token: string }
      >('/api/v1/auth/login', values)

      if ('totp_required' in data) {
        setTempToken(data.temp_token)
        setTotpRequired(true)
      } else {
        api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
        setAccessToken(data.access_token)
        setUser(data.user)
        navigate('/')
      }
    } catch {
      setError('Invalid email or password.')
    }
  }

  async function handleTotp() {
    setError(null)
    try {
      const { data } = await api.post<{ access_token: string; user: User }>(
        '/api/v1/auth/login/totp',
        { temp_token: tempToken, code: totpCode },
      )
      api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
      setAccessToken(data.access_token)
      setUser(data.user)
      navigate('/')
    } catch {
      setError('Invalid TOTP code.')
    }
  }

  if (totpRequired) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-sm space-y-6">
          <h1 className="text-2xl font-bold text-gray-900">Two-Factor Authentication</h1>
          <p className="text-sm text-gray-600">Enter the 6-digit code from your authenticator app.</p>
          <input
            type="text"
            inputMode="numeric"
            maxLength={6}
            placeholder="6-digit code"
            value={totpCode}
            onChange={(e) => setTotpCode(e.target.value)}
            className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          />
          {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
          <button
            type="button"
            onClick={handleTotp}
            className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white"
          >
            Verify
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Sign in to HabitFlow</h1>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
            <input
              id="email"
              type="email"
              {...register('email')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
            {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">Password</label>
            <input
              id="password"
              type="password"
              {...register('password')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
          {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            Log in
          </button>
        </form>
        <p className="text-center text-sm text-gray-600">
          No account?{' '}
          <Link to="/register" className="text-indigo-600 hover:underline">Register</Link>
        </p>
      </div>
    </div>
  )
}
