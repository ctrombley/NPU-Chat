import { test, expect } from '@playwright/test';

test.describe('Template Management', () => {
  test('should navigate to templates view', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /manage templates/i }).click();
    await expect(page.getByText('Default')).toBeVisible();
  });

  test('should create a new template', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /manage templates/i }).click();

    await page.getByRole('button', { name: /new template/i }).click();
    await page.getByPlaceholder(/name/i).fill('Test Template');
    await page.getByPlaceholder(/prefix/i).fill('You are a test assistant.');
    await page.getByPlaceholder(/postfix/i).fill('Be brief.');
    await page.getByRole('button', { name: /save|create|confirm/i }).click();

    await expect(page.getByText('Test Template')).toBeVisible();
  });

  test('should navigate back to chats', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /manage templates/i }).click();
    await page.getByRole('button', { name: /back to chats/i }).click();
    await expect(page.getByRole('button', { name: /new chat/i })).toBeVisible();
  });
});
