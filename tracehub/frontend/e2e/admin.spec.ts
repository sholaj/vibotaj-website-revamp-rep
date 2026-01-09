import { test, expect } from '@playwright/test';
import { login, logout, verifyLoggedIn, expectActionAvailable, verifyMenuVisibility, verifyNoConsoleErrors } from './helpers';

/**
 * ADMIN USER E2E TESTS
 *
 * Role: Full system access - user management, all data visible
 * Permissions: Manage users, view all shipments, view analytics
 *
 * Actual UI navigation (from Layout.tsx):
 * - Dashboard: visible to all (shows shipments)
 * - Analytics: visible to all
 * - Users: admin only (canManageUsers)
 * - Logout: always visible
 */

test.describe('ADMIN - System Management & Full Access', () => {
  const ADMIN_EMAIL = 'admin@vibotaj.com';

  test.beforeEach(async ({ page }) => {
    // Login before each test
    await login(page, 'admin');
    await verifyLoggedIn(page, 'admin');
  });

  test.afterEach(async ({ page }) => {
    // Logout after each test
    await logout(page);
  });

  test('should login successfully and access admin dashboard', async ({ page }) => {
    // Verify redirected to dashboard
    await expect(page).toHaveURL(/dashboard|home/);

    // Verify admin email visible in footer (format: "Logged in as admin@vibotaj.com")
    const userIndicator = page.locator(`text=Logged in as ${ADMIN_EMAIL}`);
    await expect(userIndicator).toBeVisible();

    // Verify no console errors
    const errors = await verifyNoConsoleErrors(page);
    expect(errors.length).toBe(0);
  });

  test('should show all admin menu items', async ({ page }) => {
    // Verify complete navigation menu for admin
    await verifyMenuVisibility(page, 'admin');

    // Verify admin-only Users link is visible
    const usersLink = page.locator('nav a:has-text("Users")').first();
    await expect(usersLink).toBeVisible();
  });

  test('should see shipments on dashboard', async ({ page }) => {
    // Admin should see shipments on dashboard
    // Dashboard is the main view showing shipments
    await expect(page).toHaveURL(/dashboard/);

    // Look for shipment data or table
    const dashboard = page.locator('main');
    await expect(dashboard).toBeVisible({ timeout: 10000 });
  });

  test('should be able to navigate to Users management', async ({ page }) => {
    // Click Users in nav
    const usersLink = page.locator('nav a:has-text("Users")').first();
    await usersLink.click();
    await page.waitForLoadState('networkidle');

    // Should be on users page
    await expect(page).toHaveURL(/users/);

    // Should see user-related content
    const usersPage = page.locator('main');
    await expect(usersPage).toBeVisible({ timeout: 5000 });
  });

  test('should be able to view analytics', async ({ page }) => {
    // Navigate to Analytics
    const analyticsLink = page.locator('nav a:has-text("Analytics")').first();
    await analyticsLink.click();
    await page.waitForLoadState('networkidle');

    // Should be on analytics page
    await expect(page).toHaveURL(/analytics/);

    // Should see analytics content
    const analyticsPage = page.locator('main');
    await expect(analyticsPage).toBeVisible({ timeout: 5000 });
  });

  test('should see role badge as Admin', async ({ page }) => {
    // Admin should see their role badge
    const roleBadge = page.locator('text="Admin"').first();
    await expect(roleBadge).toBeVisible({ timeout: 5000 });
  });

  test('should see logout button', async ({ page }) => {
    // Logout button should be visible
    const logoutButton = page.locator('button:has-text("Logout")').first();
    await expect(logoutButton).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    // Verify logged in first (footer format: "Logged in as {email}")
    const userIndicator = page.locator(`text=Logged in as ${ADMIN_EMAIL}`);
    await expect(userIndicator).toBeVisible();

    // Click logout
    const logoutButton = page.locator('button:has-text("Logout")').first();
    await logoutButton.click();

    // Should redirect to login
    await expect(page).toHaveURL(/login/);
  });
});
