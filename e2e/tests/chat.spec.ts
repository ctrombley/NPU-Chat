import { test, expect } from '@playwright/test';

test.describe('Chat Management', () => {
  test('should load the app', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/NPU/i);
  });

  test('should create a new chat', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /new chat/i }).click();
    await page.getByPlaceholder(/chat name/i).fill('E2E Test Chat');
    await page.keyboard.press('Enter');
    await expect(page.getByText('E2E Test Chat')).toBeVisible();
  });

  test('should switch between chats', async ({ page }) => {
    await page.goto('/');

    // Create two chats
    await page.getByRole('button', { name: /new chat/i }).click();
    await page.getByPlaceholder(/chat name/i).fill('Chat A');
    await page.keyboard.press('Enter');

    await page.getByRole('button', { name: /new chat/i }).click();
    await page.getByPlaceholder(/chat name/i).fill('Chat B');
    await page.keyboard.press('Enter');

    // Switch to first chat
    await page.getByText('Chat A').click();
    await expect(page.getByText('Chat A')).toBeVisible();
  });

  test('should delete a chat', async ({ page }) => {
    await page.goto('/');

    // Create a chat
    await page.getByRole('button', { name: /new chat/i }).click();
    await page.getByPlaceholder(/chat name/i).fill('Delete Me');
    await page.keyboard.press('Enter');
    await expect(page.getByText('Delete Me')).toBeVisible();

    // Delete it
    const chatItem = page.getByText('Delete Me').locator('..');
    await chatItem.getByRole('button', { name: /delete/i }).click();
    await expect(page.getByText('Delete Me')).not.toBeVisible();
  });

  test('should toggle favorite', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('button', { name: /new chat/i }).click();
    await page.getByPlaceholder(/chat name/i).fill('Fav Chat');
    await page.keyboard.press('Enter');

    const chatItem = page.getByText('Fav Chat').locator('..');
    const favButton = chatItem.getByRole('button', { name: /favorite/i });
    await favButton.click();
  });
});
