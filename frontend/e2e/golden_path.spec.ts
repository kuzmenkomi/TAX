import { test, expect } from '@playwright/test';
import { fileURLToPath } from 'url';

test.use({ viewport: { width: 1280, height: 800 } });

const testDataPath = fileURLToPath(new URL('./test_data.csv', import.meta.url));

test('Golden Path: Register -> Onboarding -> Import -> Calculate -> Download', async ({ page }) => {
  test.setTimeout(90000);
  const email = `test_e2e_${Date.now()}@example.com`;
  const password = `StrongE2E!${Date.now()}#kZ7`;

  page.on('requestfailed', (request) => {
    if (request.url().includes('/api/')) {
      console.log(`Request failed: ${request.method()} ${request.url()} :: ${request.failure()?.errorText}`);
    }
  });

  page.on('response', async (response) => {
    if (response.url().includes('/api/v1/auth/register')) {
      console.log(`Register response: ${response.status()} ${response.url()}`);
      if (!response.ok()) {
        console.log(`Register response body: ${await response.text().catch(() => '<unreadable>')}`);
      }
    }
  });

  console.log(`Starting Golden Path with email: ${email}`);

  // 1. Register
  await page.goto('/register');
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.locator('form button[type="submit"]').click();

  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);
  console.log(`URL after registration: ${page.url()}`);

  if (page.url().includes('/register')) {
    const pageText = await page.locator('main').textContent();
    if (pageText?.trim()) {
      console.log(`Registration stayed on page with content: ${pageText.replace(/\s+/g, ' ').trim()}`);
    }
  }

  // Fallback if redirected to login
  if (page.url().includes('login')) {
    console.log('Redirected to login, performing manual login');
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(4000);
    console.log(`URL after login: ${page.url()}`);
  }

  // 2. Handle Onboarding
  if (page.url().includes('onboarding')) {
    console.log('Step 1: Country -> Continue');
    await page.click('button:has-text("Continuar")');
    await page.waitForTimeout(2000);

    console.log('Step 2: Tax Structure -> Continue');
    await page.click('button:has-text("Continuar")');
    await page.waitForTimeout(2000);

    console.log('Step 3: Portfolio Size -> Continue');
    await page.click('button:has-text("Continuar")');

    console.log('Waiting for Dashboard redirect...');
    await page.waitForURL(/.*dashboard/, { timeout: 25000 });
  }

  // 3. Verify Dashboard and session persistence
  await expect(page).toHaveURL(/.*dashboard/);
  await expect(page.locator('aside')).toBeVisible();
  await page.reload();
  await expect(page).toHaveURL(/.*dashboard/);
  await expect(page.locator('aside')).toBeVisible();

  // 4. Navigate to Tax Optimizer
  console.log('Navigating to Tax tab');
  await page.getByRole('button', { name: /^(Impostos|Tax)$/i }).click();

  // 5. Upload CSV using the current Large Data Import flow
  console.log('Uploading CSV');
  const fileChooserPromise = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: /Select CSV Files/i }).click();
  const fileChooser = await fileChooserPromise;
  await fileChooser.setFiles(testDataPath);

  // 6. Wait for Analysis
  console.log('Waiting for analysis results...');
  await expect(page.getByText(/Audit Complete|Auditoria Completa/i)).toBeVisible({ timeout: 45000 });

  // 7. Verify Results
  await expect(page.getByText(/Executive Summary/i)).toBeVisible();
  await expect(page.getByRole('button', { name: /Comprehensive CSV/i })).toBeVisible();

  // 8. Verify export works
  console.log('Downloading export');
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: /Comprehensive CSV/i }).click();
  const download = await downloadPromise;
  expect(await download.failure()).toBeNull();

  console.log('Golden Path Success: smoke path passed.');
});
