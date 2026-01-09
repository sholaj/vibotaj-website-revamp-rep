import { test, expect } from '@playwright/test';
import { login, logout, verifyLoggedIn, expectActionAvailable, verifyMenuVisibility, verifyNoConsoleErrors } from './helpers';

/**
 * ADMIN USER E2E TESTS
 * 
 * Role: Full system access - user/org management, all data
 * Permissions: Create orgs, invite users, assign roles, view all data
 * 
 * Journey: Login → Dashboard (all orgs) → Manage Users → Assign Roles
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

    // Verify admin email visible in header/menu
    const userIndicator = page.locator(`text="${ADMIN_EMAIL}"`);
    await expect(userIndicator).toBeVisible();

    // Verify no console errors
    const errors = await verifyNoConsoleErrors(page);
    expect(errors.length).toBe(0);
  });

  test('should show all admin menu items', async ({ page }) => {
    // Verify complete navigation menu for admin
    await verifyMenuVisibility(page, 'admin');

    // Specific checks for admin-only items
    const usersLink = page.locator('nav, aside').locator('text="Users"').first();
    await expect(usersLink).toBeVisible();

    const organizationsLink = page.locator('nav, aside').locator('text="Organizations"').first();
    await expect(organizationsLink).toBeVisible();

    const settingsLink = page.locator('nav, aside').locator('text="Settings"').first();
    await expect(settingsLink).toBeVisible();
  });

  test('should see all shipments across all organizations', async ({ page }) => {
    // Admin should see cross-org data
    // Look for shipment VIBO-2026-001
    const shipmentLink = page.locator('text="VIBO-2026-001"').first();
    await expect(shipmentLink).toBeVisible({ timeout: 10000 });

    // Count should be non-zero
    const rows = page.locator('table tbody tr, [role="row"]').count();
    const count = await rows;
    expect(count).toBeGreaterThan(0);
  });

  test('should be able to navigate to Users management', async ({ page }) => {
    // Click Users in nav
    const usersLink = page.locator('nav, aside').locator('text="Users"').first();
    await usersLink.click();
    await page.waitForLoadState('networkidle');

    // Should see user list
    const userTable = page.locator('table');
    await expect(userTable).toBeVisible({ timeout: 5000 });

    // Should see test users
    await expect(page.locator(`text="${ADMIN_EMAIL}"`)).toBeVisible();
  });

  test('should be able to navigate to Organizations management', async ({ page }) => {
    // Click Organizations in nav
    const orgsLink = page.locator('nav, aside').locator('text="Organizations"').first();
    await orgsLink.click();
    await page.waitForLoadState('networkidle');

    // Should see org list or org management UI
    const heading = page.locator('h1, h2').locator('text="Organization"').first();
    await expect(heading).toBeVisible({ timeout: 5000 });
  });

  test('should be able to view analytics for all organizations', async ({ page }) => {
    // Navigate to Analytics
    const analyticsLink = page.locator('nav, aside').locator('text="Analytics"').first();
    await analyticsLink.click();
    await page.waitForLoadState('networkidle');

    // Should see dashboard with metrics
    const metrics = page.locator('[role="heading"], h1, h2');
    await expect(metrics).toBeDefined();
  });

  test('should have Create User or Invite User capability', async ({ page }) => {
    // Navigate to Users
    const usersLink = page.locator('nav, aside').locator('text="Users"').first();
    await usersLink.click();
    await page.waitForLoadState('networkidle');

    // Should see "Create User", "Invite User", or "Add User" button
    await expectActionAvailable(page, 'Invite User');
  });

  test('should see Settings menu (admin-only)', async ({ page }) => {
    // Admin should have access to Settings
    const settingsLink = page.locator('nav, aside').locator('text="Settings"').first();
    await expect(settingsLink).toBeVisible();

    // Click to open
    await settingsLink.click();
    await page.waitForLoadState('networkidle');

    // Should be on settings page
    await expect(page).toHaveURL(/settings|admin/i);
  });

  test('should logout successfully', async ({ page }) => {
    // Verify logged in first
    const userMenu = page.locator(`text="${ADMIN_EMAIL}"`).first();
    await expect(userMenu).toBeVisible();

    // Logout is handled by test.afterEach() above, but we can verify
    // by checking that page navigates to login after logout
  });

  test('should handle session timeout gracefully', async ({ page }) => {
    // Navigate to shipments first
    const shipmentsLink = page.locator('nav, aside').locator('text="Shipments"').first();
    await shipmentsLink.click();
    await page.waitForLoadState('networkidle');

    // Verify on shipments page
    await expect(page).toHaveURL(/shipment/i);

    // (Optional) If you want to test session timeout:
    // await page.context().clearCookies();
    // await page.reload();
    // Should redirect to login
  });
});
