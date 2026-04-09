import { test, expect } from '@playwright/test'
import { randomBytes } from 'crypto'

function uniqueEmail() {
  return `test_${randomBytes(4).toString('hex')}@example.com`
}

test.describe('Auth flows', () => {
  test('register a new account and land on dashboard', async ({ page }) => {
    const email = uniqueEmail()
    const username = `user_${randomBytes(3).toString('hex')}`

    await page.goto('/register')
    await page.getByLabel(/email/i).fill(email)
    await page.getByLabel(/username/i).fill(username)
    await page.getByLabel(/^password/i).fill('SecurePassword123!')
    await page.getByRole('button', { name: /register/i }).click()

    await expect(page).toHaveURL(/\/(dashboard)?$/)
    await expect(page.getByText(/welcome|dashboard/i)).toBeVisible()
  })

  test('login with valid credentials', async ({ page }) => {
    // Uses a pre-seeded test account (configured via env TEST_USER_EMAIL / TEST_USER_PASS)
    const email = process.env['TEST_USER_EMAIL'] ?? 'demo@habitflow.test'
    const password = process.env['TEST_USER_PASS'] ?? 'DemoPassword123!'

    await page.goto('/login')
    await page.getByLabel(/email/i).fill(email)
    await page.getByLabel(/password/i).fill(password)
    await page.getByRole('button', { name: /log in|sign in/i }).click()

    await expect(page).toHaveURL(/\/(dashboard)?$/)
  })

  test('shows error on invalid credentials', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/email/i).fill('wrong@example.com')
    await page.getByLabel(/password/i).fill('wrongpassword')
    await page.getByRole('button', { name: /log in|sign in/i }).click()

    await expect(page.getByRole('alert')).toBeVisible()
    await expect(page).toHaveURL(/\/login/)
  })

  test('logout clears session', async ({ page }) => {
    const email = process.env['TEST_USER_EMAIL'] ?? 'demo@habitflow.test'
    const password = process.env['TEST_USER_PASS'] ?? 'DemoPassword123!'

    await page.goto('/login')
    await page.getByLabel(/email/i).fill(email)
    await page.getByLabel(/password/i).fill(password)
    await page.getByRole('button', { name: /log in|sign in/i }).click()
    await expect(page).toHaveURL(/\/(dashboard)?$/)

    await page.getByRole('button', { name: /log out|sign out/i }).click()
    await expect(page).toHaveURL(/\/login/)
  })

  test('redirects unauthenticated users to login', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/login/)
  })
})
