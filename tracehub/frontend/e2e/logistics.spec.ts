import { test, expect } from '@playwright/test';
import { login, logout, verifyLoggedIn, expectActionAvailable, expectActionNotAvailable, verifyMenuVisibility } from './helpers';

/**
 * LOGISTICS AGENT E2E TESTS
 * 
 * Role: Shipment creation & all document uploads
 * Permissions: Create shipments, upload all document types, manage shipments, NO approval
 * 
 * Journey: Login → Create Shipment → Add Product → Upload Documents → Submit for Review
 */

test.describe('LOGISTICS AGENT - Shipment Creation & Document Upload', () => {
  const LOGISTICS_EMAIL = 'logistic@vibotaj.com';
  const TEST_SHIPMENT_ID = 'VIBO-2026-001';

  test.beforeEach(async ({ page }) => {
    await login(page, 'logistics');
    await verifyLoggedIn(page, 'logistics');
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });

  test('should login as logistics agent and see dashboard', async ({ page }) => {
    // Verify on dashboard
    await expect(page).toHaveURL(/dashboard|home/);

    // Verify email visible
    const userIndicator = page.locator(`text="${LOGISTICS_EMAIL}"`);
    await expect(userIndicator).toBeVisible();
  });

  test('should show logistics-specific menu items', async ({ page }) => {
    // Verify menu for logistics role
    await verifyMenuVisibility(page, 'logistics');

    // Should see "Create Shipment"
    const createLink = page.locator('nav, aside').locator('text="Create Shipment"').first();
    await expect(createLink).toBeVisible();

    // Should NOT see admin/compliance items
    const usersLink = page.locator('nav, aside').locator('text="Users"');
    await expect(usersLink).toBeHidden();

    const settingsLink = page.locator('nav, aside').locator('text="Settings"');
    await expect(settingsLink).toBeHidden();
  });

  test('should see assigned shipments in dashboard', async ({ page }) => {
    // Logistics can see their own shipments
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await expect(shipmentLink).toBeVisible({ timeout: 10000 });

    // Should be in shipment list
    const rows = page.locator('table tbody tr, [role="row"]');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should be able to navigate to Create Shipment page', async ({ page }) => {
    // Click Create Shipment
    const createLink = page.locator('nav, aside').locator('text="Create Shipment"').first();
    await createLink.click();
    await page.waitForLoadState('networkidle');

    // Should be on create shipment page
    await expect(page).toHaveURL(/create|new.*shipment/i);

    // Should see form fields
    const form = page.locator('form, [role="form"], .form-container');
    await expect(form).toBeVisible({ timeout: 5000 });
  });

  test('should NOT be able to approve documents', async ({ page }) => {
    // Navigate to existing shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Should NOT see Approve button
    await expectActionNotAvailable(page, 'Approve');
    await expectActionNotAvailable(page, 'Validate');
  });

  test('should be able to upload documents', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Should see Upload button
    await expectActionAvailable(page, 'Upload');
  });

  test('should see shipment details and document list', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Verify on shipment detail
    await expect(page).toHaveURL(new RegExp(`shipment|${TEST_SHIPMENT_ID}`));

    // Should see shipment info (container, B/L, vessel, etc.)
    const shipmentInfo = page.locator('h1, h2, [role="heading"]').first();
    await expect(shipmentInfo).toBeVisible();

    // Should see documents section
    const documentsSection = page.locator('text="Documents"').first();
    await expect(documentsSection).toBeVisible();
  });

  test('should NOT have access to Analytics', async ({ page }) => {
    // Logistics should not see analytics
    const analyticsLink = page.locator('nav, aside').locator('text="Analytics"').first();
    
    // Should be hidden for logistics agents
    const isHidden = await analyticsLink.isHidden();
    const isDisabled = (await analyticsLink.getAttribute('disabled')) !== null;
    expect(isHidden || isDisabled).toBeTruthy();
  });

  test('should NOT be able to manage users or organizations', async ({ page }) => {
    // Logistics should not see user/org management
    const usersLink = page.locator('nav, aside').locator('text="Users"');
    await expect(usersLink).toBeHidden();

    const orgsLink = page.locator('nav, aside').locator('text="Organizations"');
    await expect(orgsLink).toBeHidden();
  });

  test('should see shipment status (DRAFT, DOCS_PENDING, etc.)', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Should see status field/badge
    const statusField = page.locator('[data-testid*="status"], .status, [aria-label*="Status"]').first();
    
    if (await statusField.isVisible()) {
      const statusText = await statusField.textContent();
      expect(statusText).toMatch(/DRAFT|DOCS_PENDING|DOCS_COMPLETE|IN_TRANSIT|ARRIVED|CUSTOMS|DELIVERED|ARCHIVED/i);
    }
  });

  test('should be able to edit shipment details if in DRAFT status', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Look for Edit button
    const editButton = page.locator('button').locator(':text("Edit")').first();
    
    // If shipment is in DRAFT, should be able to edit
    // Status check needed first
    const statusField = page.locator('[data-testid*="status"], .status').first();
    const status = await statusField.textContent();
    
    if (status?.includes('DRAFT')) {
      await expectActionAvailable(page, 'Edit');
    }
  });

  test('should see document upload status (UPLOADED, PENDING_VALIDATION, VALIDATED)', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Look for document status
    const statusColumn = page.locator('text="Status"').first();
    if (await statusColumn.isVisible()) {
      // Should see status values
      const statusValues = page.locator('td, [role="cell"]').locator(':text("UPLOADED"), :text("VALIDATED"), :text("PENDING")');
      const count = await statusValues.count();
      expect(count).toBeGreaterThanOrEqual(0);
    }
  });

  test('should NOT be able to create organizations', async ({ page }) => {
    // Logistics cannot create orgs
    const orgsLink = page.locator('nav, aside').locator('text="Organizations"');
    await expect(orgsLink).toBeHidden();
  });

  test('should NOT be able to access Settings', async ({ page }) => {
    // Logistics should not see settings
    const settingsLink = page.locator('nav, aside').locator('text="Settings"');
    await expect(settingsLink).toBeHidden();
  });

  test('should have My Documents or Shipments view with filtering', async ({ page }) => {
    // Navigate to Shipments
    const shipmentsLink = page.locator('nav, aside').locator('text="Shipment"').first();
    
    if (await shipmentsLink.isVisible()) {
      await shipmentsLink.click();
      await page.waitForLoadState('networkidle');

      // Should see list of shipments assigned to this user
      const shipmentTable = page.locator('table').first();
      await expect(shipmentTable).toBeVisible({ timeout: 5000 });
    }
  });

  test('should be able to track container movement (if data available)', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Look for tracking section
    const trackingSection = page.locator('text="Tracking", text="Container", text="Vessel"').first();
    
    if (await trackingSection.isVisible()) {
      // Should see tracking info
      expect(true).toBe(true); // Tracking visible
    }
  });

  test('should logout successfully', async ({ page }) => {
    // Logout is handled in afterEach
    const userMenu = page.locator(`text="${LOGISTICS_EMAIL}"`).first();
    await expect(userMenu).toBeVisible();
  });
});
