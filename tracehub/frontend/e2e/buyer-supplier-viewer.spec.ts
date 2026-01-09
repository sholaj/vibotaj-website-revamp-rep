import { test, expect } from '@playwright/test';
import { login, logout, verifyLoggedIn, verifyMenuVisibility } from './helpers';

/**
 * BUYER E2E TESTS
 *
 * Role: Read-only access to assigned shipments
 * Permissions: View dashboard, view analytics, no user management
 *
 * Actual UI navigation (from Layout.tsx):
 * - Dashboard: visible to all
 * - Analytics: visible to all
 * - Users: NOT visible (admin only)
 * - Logout: always visible
 */

test.describe('BUYER - Read-Only Shipment Monitoring', () => {
  const BUYER_EMAIL = 'buyer@witatrade.de';

  test.beforeEach(async ({ page }) => {
    await login(page, 'buyer');
    await verifyLoggedIn(page, 'buyer');
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });

  test('should login as buyer and see dashboard', async ({ page }) => {
    // Verify on dashboard
    await expect(page).toHaveURL(/dashboard|home/);

    // Verify email visible in footer
    const userIndicator = page.locator(`text=Logged in as ${BUYER_EMAIL}`);
    await expect(userIndicator).toBeVisible();
  });

  test('should show buyer-specific menu items', async ({ page }) => {
    // Verify menu for buyer role
    await verifyMenuVisibility(page, 'buyer');

    // Should see Dashboard
    const dashboardLink = page.locator('nav a:has-text("Dashboard")').first();
    await expect(dashboardLink).toBeVisible();

    // Should see Analytics
    const analyticsLink = page.locator('nav a:has-text("Analytics")').first();
    await expect(analyticsLink).toBeVisible();
  });

  test('should NOT see Users menu (admin-only)', async ({ page }) => {
    // Buyer cannot see admin-only items
    const usersLink = page.locator('nav a:has-text("Users")');
    await expect(usersLink).toBeHidden();
  });

  test('should see dashboard content', async ({ page }) => {
    // Buyer can view dashboard
    await expect(page).toHaveURL(/dashboard/);

    // Should see main content
    const dashboard = page.locator('main');
    await expect(dashboard).toBeVisible({ timeout: 10000 });
  });

  test('should see role badge as Buyer', async ({ page }) => {
    // Buyer should see their role badge
    const roleBadge = page.locator('text="Buyer"').first();
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

  test('should logout successfully', async ({ page }) => {
    // Verify logged in first (footer format: "Logged in as {email}")
    const userIndicator = page.locator(`text=Logged in as ${BUYER_EMAIL}`);
    await expect(userIndicator).toBeVisible();

    // Click logout
    const logoutButton = page.locator('button:has-text("Logout")').first();
    await logoutButton.click();

    // Should redirect to login
    await expect(page).toHaveURL(/login/);
  });
});

/**
 * SUPPLIER E2E TESTS
 *
 * Role: Upload origin certificates, provide geolocation (when implemented)
 * Permissions: View dashboard, view analytics, no user management
 *
 * Actual UI navigation (from Layout.tsx):
 * - Dashboard: visible to all
 * - Analytics: visible to all
 * - Users: NOT visible (admin only)
 * - Logout: always visible
 */

test.describe('SUPPLIER - Origin Verification & Document Upload', () => {
  const SUPPLIER_EMAIL = 'supplier@vibotaj.com';

  test.beforeEach(async ({ page }) => {
    await login(page, 'supplier');
    await verifyLoggedIn(page, 'supplier');
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });

  test('should login as supplier and see dashboard', async ({ page }) => {
    // Verify on dashboard
    await expect(page).toHaveURL(/dashboard|home/);

    // Verify email visible in footer
    const userIndicator = page.locator(`text=Logged in as ${SUPPLIER_EMAIL}`);
    await expect(userIndicator).toBeVisible();
  });

  test('should show supplier-specific menu items', async ({ page }) => {
    // Verify menu for supplier role
    await verifyMenuVisibility(page, 'supplier');

    // Should see Dashboard
    const dashboardLink = page.locator('nav a:has-text("Dashboard")').first();
    await expect(dashboardLink).toBeVisible();

    // Should see Analytics
    const analyticsLink = page.locator('nav a:has-text("Analytics")').first();
    await expect(analyticsLink).toBeVisible();
  });

  test('should NOT see Users menu (admin-only)', async ({ page }) => {
    // Supplier cannot see admin-only items
    const usersLink = page.locator('nav a:has-text("Users")');
    await expect(usersLink).toBeHidden();
  });

  test('should see dashboard content', async ({ page }) => {
    // Supplier can view dashboard
    await expect(page).toHaveURL(/dashboard/);

    // Should see main content
    const dashboard = page.locator('main');
    await expect(dashboard).toBeVisible({ timeout: 10000 });
  });

  test('should see role badge as Supplier', async ({ page }) => {
    // Supplier should see their role badge
    const roleBadge = page.locator('text="Supplier"').first();
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

  test('should logout successfully', async ({ page }) => {
    // Verify logged in first (footer format: "Logged in as {email}")
    const userIndicator = page.locator(`text=Logged in as ${SUPPLIER_EMAIL}`);
    await expect(userIndicator).toBeVisible();

    // Click logout
    const logoutButton = page.locator('button:has-text("Logout")').first();
    await logoutButton.click();

    // Should redirect to login
    await expect(page).toHaveURL(/login/);
  });
});

/**
 * VIEWER E2E TESTS
 *
 * Role: Read-only access to ALL data (audit/compliance review)
 * Permissions: View dashboard, view analytics, no user management
 *
 * Actual UI navigation (from Layout.tsx):
 * - Dashboard: visible to all
 * - Analytics: visible to all
 * - Users: NOT visible (admin only)
 * - Logout: always visible
 */

test.describe('VIEWER - Read-Only Global Audit Access', () => {
  const VIEWER_EMAIL = 'viewer@vibotaj.com';

  test.beforeEach(async ({ page }) => {
    await login(page, 'viewer');
    await verifyLoggedIn(page, 'viewer');
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });

  test('should login as viewer and see dashboard', async ({ page }) => {
    // Verify on dashboard
    await expect(page).toHaveURL(/dashboard|home/);

    // Verify email visible in footer
    const userIndicator = page.locator(`text=Logged in as ${VIEWER_EMAIL}`);
    await expect(userIndicator).toBeVisible();
  });

  test('should show viewer-specific menu items', async ({ page }) => {
    // Verify menu for viewer role
    await verifyMenuVisibility(page, 'viewer');

    // Should see Dashboard
    const dashboardLink = page.locator('nav a:has-text("Dashboard")').first();
    await expect(dashboardLink).toBeVisible();

    // Should see Analytics
    const analyticsLink = page.locator('nav a:has-text("Analytics")').first();
    await expect(analyticsLink).toBeVisible();
  });

  test('should NOT see Users menu (admin-only)', async ({ page }) => {
    // Viewer cannot see admin-only items
    const usersLink = page.locator('nav a:has-text("Users")');
    await expect(usersLink).toBeHidden();
  });

  test('should see dashboard content', async ({ page }) => {
    // Viewer can view dashboard
    await expect(page).toHaveURL(/dashboard/);

    // Should see main content
    const dashboard = page.locator('main');
    await expect(dashboard).toBeVisible({ timeout: 10000 });
  });

  test('should see role badge as Viewer', async ({ page }) => {
    // Viewer should see their role badge
    const roleBadge = page.locator('text="Viewer"').first();
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

  test('should logout successfully', async ({ page }) => {
    // Verify logged in first (footer format: "Logged in as {email}")
    const userIndicator = page.locator(`text=Logged in as ${VIEWER_EMAIL}`);
    await expect(userIndicator).toBeVisible();

    // Click logout
    const logoutButton = page.locator('button:has-text("Logout")').first();
    await logoutButton.click();

    // Should redirect to login
    await expect(page).toHaveURL(/login/);
  });
});
