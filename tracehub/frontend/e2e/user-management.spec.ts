/**
 * E2E Tests for Admin User Management
 *
 * Verifies that admin users can access and use the Users page.
 * Tests navigation, access control, and basic page visibility.
 */

import { test, expect } from '@playwright/test';
import { login, logout, verifyLoggedIn } from './helpers';

test.describe('Admin User Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await login(page, 'admin');
    await verifyLoggedIn(page, 'admin');
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });

  test('admin can access user management page via nav link', async ({ page }) => {
    // Navigate to users page via nav link
    const usersLink = page.locator('nav a:has-text("Users")').first();
    await expect(usersLink).toBeVisible();
    await usersLink.click();
    await page.waitForLoadState('networkidle');

    // Verify on users page
    await expect(page).toHaveURL(/users/);

    // Verify page loaded - main content visible
    const mainContent = page.locator('main');
    await expect(mainContent).toBeVisible({ timeout: 5000 });
  });

  test('admin can navigate directly to users page', async ({ page }) => {
    // Navigate directly to users page
    await page.goto('/users');
    await page.waitForLoadState('networkidle');

    // Verify on users page
    await expect(page).toHaveURL(/users/);

    // Should see main content
    const mainContent = page.locator('main');
    await expect(mainContent).toBeVisible({ timeout: 5000 });
  });

  test('admin sees user list on users page', async ({ page }) => {
    // Navigate to users page
    await page.goto('/users');
    await page.waitForLoadState('networkidle');

    // Should see user-related content
    const mainContent = page.locator('main');
    await expect(mainContent).toBeVisible({ timeout: 5000 });

    // Admin email should be visible somewhere on the page
    const adminEmail = page.locator('text="admin@vibotaj.com"');
    await expect(adminEmail).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Non-Admin User Management Access', () => {
  test('compliance officer cannot see Users nav link', async ({ page }) => {
    await login(page, 'compliance');
    await verifyLoggedIn(page, 'compliance');

    // Users link should be hidden
    const usersLink = page.locator('nav a:has-text("Users")');
    await expect(usersLink).toBeHidden();

    await logout(page);
  });

  test('logistics agent cannot see Users nav link', async ({ page }) => {
    await login(page, 'logistics');
    await verifyLoggedIn(page, 'logistics');

    // Users link should be hidden
    const usersLink = page.locator('nav a:has-text("Users")');
    await expect(usersLink).toBeHidden();

    await logout(page);
  });

  test('viewer cannot see Users nav link', async ({ page }) => {
    await login(page, 'viewer');
    await verifyLoggedIn(page, 'viewer');

    // Users link should be hidden
    const usersLink = page.locator('nav a:has-text("Users")');
    await expect(usersLink).toBeHidden();

    await logout(page);
  });
});
