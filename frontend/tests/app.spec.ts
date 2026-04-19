import { expect, test } from '@playwright/test'

test('renders the MedDash workspace shell', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'MedDash' })).toBeVisible()
  await expect(page.getByText('Clinician-assistive command center')).toBeVisible()

  await page.getByRole('tab', { name: /Patient Consultation/i }).click()
  await expect(page.getByText('Multi-agent consultation stream')).toBeVisible()

  await page.getByRole('tab', { name: /Knowledge/i }).click()
  await expect(page.getByText(/^Evidence retrieval$/)).toBeVisible()

  await page.getByRole('tab', { name: /Settings/i }).click()
  await expect(page.getByText('Provider and prompt routing')).toBeVisible()
})

test('runs a real consultation against the backend', async ({ page }) => {
  await page.goto('/')

  await page.getByRole('tab', { name: /Patient Consultation/i }).click()
  await Promise.all([
    page.waitForResponse((response) => {
      return response.url().includes('/api/consult/start') && response.status() === 200
    }),
    page.getByRole('button', { name: /Start real consultation/i }).click(),
  ])

  await expect(page.getByRole('button', { name: /Send follow-up/i })).toBeEnabled()
  await expect(page.getByRole('row', { name: /Allergies : penicillin/i })).toBeVisible()
  await expect(
    page.getByRole('row', { name: /Red flags : chest pain, shortness of breath/i })
  ).toBeVisible()

  await Promise.all([
    page.waitForResponse((response) => {
      return response.url().includes('/api/consult/chat') && response.status() === 200
    }),
    page.getByRole('button', { name: /Send follow-up/i }).click(),
  ])
  await expect(
    page.getByRole('row', { name: /Disposition flag : needs_handoff/i })
  ).toBeVisible()

  await page.getByRole('tab', { name: /Diagnosis & Treatment/i }).click()
  await expect(page.getByText(/amoxicillin safety alert/i)).toBeVisible()
})
