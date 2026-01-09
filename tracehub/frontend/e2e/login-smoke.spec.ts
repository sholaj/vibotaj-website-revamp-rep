/**
 * Quick smoke test for login functionality
 */
import { test, expect } from '@playwright/test';
import { login } from './helpers';

test.describe('Login Smoke Test', () => {
  test('admin should login successfully', async ({ page }) => {
    await login(page, 'admin');
    await expect(page).toHaveURL(/dashboard/);
    await expect(page.locator('body')).toBeVisible();
  });

  test('compliance should login successfully', async ({ page }) => {
    await login(page, 'compliance');
    await expect(page).toHaveURL(/dashboard/);
  });

  test('logistics should login successfully', async ({ page }) => {
    await login(page, 'logistics');
    await expect(page).toHaveURL(/dashboard/);
  });

  test('buyer should login successfully', async ({ page }) => {
    await login(page, 'buyer');
    await expect(page).toHaveURL(/dashboard/);
  });

  test('supplier should login successfully', async ({ page }) => {
    await login(page, 'supplier');
    await expect(page).toHaveURL(/dashboard/);
  });

  test('viewer should login successfully', async ({ page }) => {
    await login(page, 'viewer');
    await expect(page).toHaveURL(/dashboard/);
  });
});
