import { test, expect } from '@playwright/test';
import { login, logout, verifyLoggedIn, verifyMenuVisibility } from './helpers';

/**
 * COMPLIANCE OFFICER E2E TESTS
 *
 * Role: Document validation & approval authority
 * Permissions: View shipments, view analytics, no user management
 *
 * Actual UI navigation (from Layout.tsx):
 * - Dashboard: visible to all (shows shipments)
 * - Analytics: visible to all
 * - Users: NOT visible (admin only)
 * - Logout: always visible
 */

test.describe('COMPLIANCE - Document Validation & Approval', () => {
  const COMPLIANCE_EMAIL = 'compliance@vibotaj.com';

  test.beforeEach(async ({ page }) => {
    await login(page, 'compliance');
    await verifyLoggedIn(page, 'compliance');
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });

  test('should login as compliance officer and see dashboard', async ({ page }) => {
    // Verify on dashboard
    await expect(page).toHaveURL(/dashboard|home/);

    // Verify email visible in footer
    const userIndicator = page.locator(`text=Logged in as ${COMPLIANCE_EMAIL}`);
    await expect(userIndicator).toBeVisible();
  });

  test('should show compliance-specific menu items', async ({ page }) => {
    // Verify menu for compliance role
    await verifyMenuVisibility(page, 'compliance');

    // Verify Dashboard is visible
    const dashboardLink = page.locator('nav a:has-text("Dashboard")').first();
    await expect(dashboardLink).toBeVisible();

    // Verify Analytics is visible
    const analyticsLink = page.locator('nav a:has-text("Analytics")').first();
    await expect(analyticsLink).toBeVisible();
  });

  test('should NOT see Users menu (admin-only)', async ({ page }) => {
    // Compliance cannot see admin-only items
    const usersLink = page.locator('nav a:has-text("Users")');
    await expect(usersLink).toBeHidden();
  });

  test('should see dashboard content', async ({ page }) => {
    // Compliance can view dashboard
    await expect(page).toHaveURL(/dashboard/);

    // Should see main content
    const dashboard = page.locator('main');
    await expect(dashboard).toBeVisible({ timeout: 10000 });
  });

  test('should see role badge as Compliance', async ({ page }) => {
    // Compliance officer should see their role badge
    const roleBadge = page.locator('text="Compliance"').first();
    await expect(roleBadge).toBeVisible({ timeout: 5000 });
  });

  test('should be able to navigate to Analytics', async ({ page }) => {
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

  test('should see logout button', async ({ page }) => {
    // Logout button should be visible
    const logoutButton = page.locator('button:has-text("Logout")').first();
    await expect(logoutButton).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    // Verify logged in first (footer format: "Logged in as {email}")
    const userIndicator = page.locator(`text=Logged in as ${COMPLIANCE_EMAIL}`);
    await expect(userIndicator).toBeVisible();

    // Click logout
    const logoutButton = page.locator('button:has-text("Logout")').first();
    await logoutButton.click();

    // Should redirect to login
    await expect(page).toHaveURL(/login/);
  });
});
