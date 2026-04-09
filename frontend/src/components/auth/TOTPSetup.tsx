import { useState } from 'react'
import api from '@/lib/api'

interface TOTPSetupData {
  secret: string
  qr_uri: string
  backup_codes: string[]
}

interface TOTPSetupProps {
  onComplete: () => void
}

export function TOTPSetup({ onComplete }: TOTPSetupProps) {
  const [setupData, setSetupData] = useState<TOTPSetupData | null>(null)
  const [code, setCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSetup() {
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.post<TOTPSetupData>('/api/v1/auth/totp/setup')
      setSetupData(data)
    } catch {
      setError('Failed to start 2FA setup. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  async function handleVerify() {
    setLoading(true)
    setError(null)
    try {
      await api.post('/api/v1/auth/totp/verify', { code })
      onComplete()
    } catch {
      setError('Invalid code. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (!setupData) {
    return (
      <button
        type="button"
        onClick={handleSetup}
        disabled={loading}
        className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        Set up 2FA
      </button>
    )
  }

  return (
    <div className="space-y-4">
      <div>
        <p className="text-sm text-gray-600">
          Scan the QR code with your authenticator app, or enter the secret manually:
        </p>
        <code className="mt-1 block rounded bg-gray-100 px-2 py-1 text-sm font-mono">
          {setupData.secret}
        </code>
      </div>

      <div>
        <p className="text-sm text-gray-600">QR URI (paste into authenticator if needed):</p>
        <code className="mt-1 block truncate rounded bg-gray-100 px-2 py-1 text-xs font-mono">
          {setupData.qr_uri}
        </code>
      </div>

      <div className="space-y-2">
        <label htmlFor="totp-code" className="block text-sm font-medium text-gray-700">
          Enter the 6-digit code to confirm
        </label>
        <input
          id="totp-code"
          type="text"
          inputMode="numeric"
          maxLength={6}
          placeholder="6-digit code"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}

      <button
        type="button"
        onClick={handleVerify}
        disabled={loading || code.length !== 6}
        className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        Verify
      </button>
    </div>
  )
}
