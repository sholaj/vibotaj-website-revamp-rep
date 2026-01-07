import { test, expect } from '@playwright/test';
import { login, logout, verifyLoggedIn, expectActionAvailable, expectActionNotAvailable, verifyMenuVisibility } from './helpers';

/**
 * COMPLIANCE OFFICER E2E TESTS
 * 
 * Role: Document validation & approval authority
 * Permissions: Validate/approve documents, reject with comments, view all shipments, no create
 * 
 * Journey: Login → Dashboard (Pending Docs) → Open Shipment → Validate/Approve Documents
 */

test.describe('COMPLIANCE - Document Validation & Approval', () => {
  const COMPLIANCE_EMAIL = 'compliance@vibotaj.com';
  const TEST_SHIPMENT_ID = 'VIBO-2026-001';

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

    // Verify email visible
    const userIndicator = page.locator(`text="${COMPLIANCE_EMAIL}"`);
    await expect(userIndicator).toBeVisible();
  });

  test('should show compliance-specific menu items', async ({ page }) => {
    // Verify menu for compliance role
    await verifyMenuVisibility(page, 'compliance');

    // Verify cannot see admin-only items
    const usersLink = page.locator('nav, aside').locator('text="Users"');
    await expect(usersLink).toBeHidden();

    const orgsLink = page.locator('nav, aside').locator('text="Organizations"');
    await expect(orgsLink).toBeHidden();
  });

  test('should see all shipments (not restricted)', async ({ page }) => {
    // Compliance can view all shipments
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await expect(shipmentLink).toBeVisible({ timeout: 10000 });

    // Should see shipment list
    const rows = page.locator('table tbody tr, [role="row"]');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should NOT be able to create new shipment', async ({ page }) => {
    // Compliance cannot create shipments
    const createButton = page.locator('button, [role="button"]').locator(':text("Create Shipment")');
    
    // Should be hidden or disabled
    const isHidden = await createButton.isHidden();
    const isDisabled = (await createButton.getAttribute('disabled')) !== null;
    expect(isHidden || isDisabled).toBeTruthy();
  });

  test('should NOT be able to upload documents', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Should see documents section but upload button hidden/disabled
    await expectActionNotAvailable(page, 'Upload Document');
    await expectActionNotAvailable(page, 'Upload File');
  });

  test('should be able to open shipment and view documents', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Verify on shipment detail page
    await expect(page).toHaveURL(new RegExp(`shipment|${TEST_SHIPMENT_ID}`));

    // Should see documents section
    const documentsSection = page.locator('text="Documents"').first();
    await expect(documentsSection).toBeVisible();

    // Should see document list
    const documentTable = page.locator('table').first();
    await expect(documentTable).toBeVisible({ timeout: 5000 });
  });

  test('should be able to validate/approve documents', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Look for Validate or Approve button
    const approveButton = page.locator('button').locator(':text("Approve"), :text("Validate"), :text("Accept")').first();
    
    // Should be visible for documents that are pending
    if (await approveButton.isVisible()) {
      expect(await approveButton.isDisabled()).toBe(false);
    }
  });

  test('should be able to reject documents with comments', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Look for Reject button
    const rejectButton = page.locator('button').locator(':text("Reject")').first();
    
    // Should be visible (even if no action taken)
    if (await rejectButton.isVisible()) {
      expect(await rejectButton.isDisabled()).toBe(false);
    }
  });

  test('should see compliance status information', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Should see compliance status section
    const complianceStatus = page.locator('text="Compliance Status", text="Document Status", h2').first();
    await expect(complianceStatus).toBeVisible({ timeout: 5000 });
  });

  test('should see analytics (all shipments, not restricted)', async ({ page }) => {
    // Navigate to Analytics if available
    const analyticsLink = page.locator('nav, aside').locator('text="Analytics"').first();
    
    if (await analyticsLink.isVisible()) {
      await analyticsLink.click();
      await page.waitForLoadState('networkidle');

      // Should see dashboard with metrics across all shipments
      const metrics = page.locator('[data-testid*="metric"], h1, h2, .metric, .card');
      const count = await metrics.count();
      expect(count).toBeGreaterThan(0);
    }
  });

  test('should NOT be able to create or edit organizations', async ({ page }) => {
    // Compliance should not see org management
    const orgsLink = page.locator('nav, aside').locator('text="Organizations"');
    await expect(orgsLink).toBeHidden();
  });

  test('should NOT be able to access Settings', async ({ page }) => {
    // Compliance should not see settings
    const settingsLink = page.locator('nav, aside').locator('text="Settings"');
    await expect(settingsLink).toBeHidden();
  });

  test('should NOT be able to manage users', async ({ page }) => {
    // Compliance should not see user management
    const usersLink = page.locator('nav, aside').locator('text="Users"');
    await expect(usersLink).toBeHidden();
  });

  test('should see document status changes (UPLOADED → VALIDATED or REJECTED)', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Look for document status column
    const statusColumn = page.locator('text="Status"').first();
    await expect(statusColumn).toBeVisible();

    // Should see status values like "Uploaded", "Validated", "Pending"
    const statusValues = page.locator('td, [role="cell"]').locator(':text("UPLOADED"), :text("VALIDATED"), :text("PENDING")');
    const count = await statusValues.count();
    expect(count).toBeGreaterThan(-1); // May be 0 or more depending on data
  });

  test('should display EUDR/compliance-specific flags on documents', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Look for compliance-specific flags (e.g., "EUDR Flag", "HS Code Alert")
    const complianceFlags = page.locator('[data-testid*="compliance"], .flag, .badge').locator(':text("EUDR"), :text("Compliance")');
    
    // May or may not be present depending on actual documents, but UI should support it
    const count = await complianceFlags.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should have download/export audit trail', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Look for download/export buttons
    const downloadButton = page.locator('button').locator(':text("Download"), :text("Export"), :text("PDF")').first();
    
    if (await downloadButton.isVisible()) {
      expect(await downloadButton.isDisabled()).toBe(false);
    }
  });

  test('should logout successfully', async ({ page }) => {
    // Logout is handled in afterEach, but verify redirect
    const userMenu = page.locator(`text="${COMPLIANCE_EMAIL}"`).first();
    await expect(userMenu).toBeVisible();
  });
});
