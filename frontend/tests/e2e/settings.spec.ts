import { test, expect } from '@playwright/test'

test.describe('Settings flows', () => {
  test.beforeEach(async ({ page }) => {
    const email = process.env['TEST_USER_EMAIL'] ?? 'demo@habitflow.test'
    const password = process.env['TEST_USER_PASS'] ?? 'DemoPassword123!'

    await page.goto('/login')
    await page.getByLabel(/email/i).fill(email)
    await page.getByLabel(/password/i).fill(password)
    await page.getByRole('button', { name: /log in|sign in/i }).click()
    await expect(page).toHaveURL(/\/(dashboard)?$/)
  })

  test('settings page loads with profile section', async ({ page }) => {
    await page.goto('/settings')
    await expect(page.getByRole('heading', { name: /settings|profile/i })).toBeVisible()
  })

  test('update ntfy configuration', async ({ page }) => {
    await page.goto('/settings')

    // Fill in ntfy settings
    await page.getByLabel(/ntfy url/i).fill('https://ntfy.sh')
    await page.getByLabel(/ntfy topic/i).fill('my-private-topic')
    await page.getByRole('button', { name: /save|update/i }).click()

    await expect(page.getByText(/saved|updated/i)).toBeVisible()
  })

  test('2FA setup flow is visible in settings', async ({ page }) => {
    await page.goto('/settings')
    await expect(page.getByRole('button', { name: /set up 2fa|enable 2fa/i })).toBeVisible()
  })

  test('initiate 2FA setup shows QR and secret', async ({ page }) => {
    await page.goto('/settings')
    await page.getByRole('button', { name: /set up 2fa|enable 2fa/i }).click()

    // After clicking, secret or QR URI should appear
    await expect(
      page.getByText(/secret|otpauth/i).first(),
    ).toBeVisible({ timeout: 10_000 })
  })

  test('change password with valid current password', async ({ page }) => {
    const currentPass = process.env['TEST_USER_PASS'] ?? 'DemoPassword123!'

    await page.goto('/settings')
    await page.getByLabel(/current password/i).fill(currentPass)
    await page.getByLabel(/new password/i).fill(currentPass) // same — just testing the form submits
    await page.getByLabel(/confirm.*password/i).fill(currentPass)
    await page.getByRole('button', { name: /change password|update password/i }).click()

    // Either success message or no error
    await expect(page.getByRole('alert')).not.toBeVisible()
  })

  test('change timezone setting', async ({ page }) => {
    await page.goto('/settings')

    const tzSelect = page.getByLabel(/timezone/i)
    await tzSelect.selectOption('America/New_York')
    await page.getByRole('button', { name: /save|update/i }).click()

    await expect(page.getByText(/saved|updated/i)).toBeVisible()
  })
})
