import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { TOTPSetup } from '@/components/auth/TOTPSetup'

const profileSchema = z.object({
  username: z.string().min(3).max(50),
  timezone: z.string(),
  ntfy_url: z.string().url().optional().or(z.literal('')),
  ntfy_topic: z.string().optional(),
  ntfy_token: z.string().optional(),
})
type ProfileValues = z.infer<typeof profileSchema>

const passwordSchema = z.object({
  current_password: z.string().min(1),
  new_password: z.string().min(8),
  confirm_password: z.string().min(8),
}).refine((d) => d.new_password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
})
type PasswordValues = z.infer<typeof passwordSchema>

const TIMEZONES = [
  'UTC', 'America/New_York', 'America/Chicago', 'America/Denver',
  'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 'Asia/Tokyo',
  'Australia/Sydney',
]

export function SettingsPage() {
  const { user, setUser } = useAuthStore()
  const [profileSaved, setProfileSaved] = useState(false)
  const [profileError, setProfileError] = useState<string | null>(null)
  const [show2FA, setShow2FA] = useState(false)

  const { register: regProfile, handleSubmit: submitProfile } = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      username: user?.username ?? '',
      timezone: user?.timezone ?? 'UTC',
      ntfy_url: '',
      ntfy_topic: '',
      ntfy_token: '',
    },
  })

  const { register: regPassword, handleSubmit: submitPassword, formState: { errors: pwErrors } } =
    useForm<PasswordValues>({ resolver: zodResolver(passwordSchema) })

  async function onProfileSave(values: ProfileValues) {
    setProfileError(null)
    try {
      const { data } = await api.patch('/api/v1/users/me', values)
      setUser(data)
      setProfileSaved(true)
      setTimeout(() => setProfileSaved(false), 3000)
    } catch {
      setProfileError('Failed to save settings.')
    }
  }

  async function onPasswordChange(values: PasswordValues) {
    await api.patch('/api/v1/users/me/password', {
      current_password: values.current_password,
      new_password: values.new_password,
    })
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-8 space-y-10">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

      {/* Profile */}
      <section className="rounded-lg border border-gray-200 p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Profile</h2>
        <form onSubmit={submitProfile(onProfileSave)} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700">Username</label>
            <input id="username" {...regProfile('username')} className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label htmlFor="timezone" className="block text-sm font-medium text-gray-700">Timezone</label>
            <select id="timezone" {...regProfile('timezone')} className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm">
              {TIMEZONES.map((tz) => <option key={tz} value={tz}>{tz}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="ntfy_url" className="block text-sm font-medium text-gray-700">ntfy URL</label>
            <input id="ntfy_url" type="url" placeholder="https://ntfy.sh" {...regProfile('ntfy_url')} className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label htmlFor="ntfy_topic" className="block text-sm font-medium text-gray-700">ntfy Topic</label>
            <input id="ntfy_topic" {...regProfile('ntfy_topic')} className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label htmlFor="ntfy_token" className="block text-sm font-medium text-gray-700">ntfy Token (optional)</label>
            <input id="ntfy_token" {...regProfile('ntfy_token')} className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
          </div>
          {profileError && <p role="alert" className="text-sm text-red-600">{profileError}</p>}
          {profileSaved && <p className="text-sm text-green-600">Settings saved</p>}
          <button type="submit" className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
            Save
          </button>
        </form>
      </section>

      {/* 2FA */}
      <section className="rounded-lg border border-gray-200 p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Two-Factor Authentication</h2>
        {user?.totp_enabled ? (
          <p className="text-sm text-green-600">2FA is enabled on your account.</p>
        ) : show2FA ? (
          <TOTPSetup onComplete={() => { setShow2FA(false) }} />
        ) : (
          <button
            type="button"
            onClick={() => setShow2FA(true)}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Set up 2FA
          </button>
        )}
      </section>

      {/* Change password */}
      <section className="rounded-lg border border-gray-200 p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Change Password</h2>
        <form onSubmit={submitPassword(onPasswordChange)} className="space-y-4">
          <div>
            <label htmlFor="current_password" className="block text-sm font-medium text-gray-700">Current password</label>
            <input id="current_password" type="password" {...regPassword('current_password')} className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label htmlFor="new_password" className="block text-sm font-medium text-gray-700">New password</label>
            <input id="new_password" type="password" {...regPassword('new_password')} className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700">Confirm new password</label>
            <input id="confirm_password" type="password" {...regPassword('confirm_password')} className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
            {pwErrors.confirm_password && <p className="mt-1 text-xs text-red-600">{pwErrors.confirm_password.message}</p>}
          </div>
          <button type="submit" className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
            Change password
          </button>
        </form>
      </section>
    </main>
  )
}
