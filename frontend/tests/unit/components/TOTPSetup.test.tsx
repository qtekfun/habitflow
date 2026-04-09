import { describe, it, expect, vi, beforeAll, afterEach, afterAll } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { server } from '@/tests/msw/server'
import { TOTPSetup } from '@/components/auth/TOTPSetup'

const mockSetupData = {
  secret: 'JBSWY3DPEHPK3PXP',
  qr_uri: 'otpauth://totp/HabitFlow:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=HabitFlow',
  backup_codes: ['abc123', 'def456'],
}

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('TOTPSetup', () => {
  beforeEach(() => {
    server.use(
      http.post('/api/v1/auth/totp/setup', () => HttpResponse.json(mockSetupData)),
      http.post('/api/v1/auth/totp/verify', () => HttpResponse.json({ message: '2FA enabled' })),
    )
  })

  it('renders the setup initiation button', () => {
    render(<TOTPSetup onComplete={vi.fn()} />)
    expect(screen.getByRole('button', { name: /set up 2fa/i })).toBeInTheDocument()
  })

  it('shows QR code URI and secret after clicking setup', async () => {
    render(<TOTPSetup onComplete={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: /set up 2fa/i }))
    await waitFor(() => {
      expect(screen.getByText(mockSetupData.secret)).toBeInTheDocument()
    })
  })

  it('shows verify input after loading setup data', async () => {
    render(<TOTPSetup onComplete={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: /set up 2fa/i }))
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/6.digit code/i)).toBeInTheDocument()
    })
  })

  it('calls onComplete after successful verification', async () => {
    const onComplete = vi.fn()
    render(<TOTPSetup onComplete={onComplete} />)
    await userEvent.click(screen.getByRole('button', { name: /set up 2fa/i }))
    await waitFor(() => screen.getByPlaceholderText(/6.digit code/i))
    await userEvent.type(screen.getByPlaceholderText(/6.digit code/i), '123456')
    await userEvent.click(screen.getByRole('button', { name: /verify/i }))
    await waitFor(() => expect(onComplete).toHaveBeenCalled())
  })

  it('shows an error message on failed verification', async () => {
    server.use(
      http.post('/api/v1/auth/totp/verify', () =>
        HttpResponse.json({ detail: 'Invalid code' }, { status: 400 }),
      ),
    )
    render(<TOTPSetup onComplete={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: /set up 2fa/i }))
    await waitFor(() => screen.getByPlaceholderText(/6.digit code/i))
    await userEvent.type(screen.getByPlaceholderText(/6.digit code/i), '000000')
    await userEvent.click(screen.getByRole('button', { name: /verify/i }))
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
  })
})
