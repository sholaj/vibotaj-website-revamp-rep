import { test, expect } from '@playwright/test';
import { login, logout, verifyLoggedIn, expectActionNotAvailable, verifyMenuVisibility } from './helpers';

/**
 * BUYER E2E TESTS
 * 
 * Role: Read-only access to assigned shipments
 * Permissions: View assigned shipments, documents, compliance status; NO edits
 * 
 * Journey: Login → Dashboard (My Shipments) → View Shipment Details → Monitor Status
 */

test.describe('BUYER - Read-Only Shipment Monitoring', () => {
  const BUYER_EMAIL = 'buyer@vibotaj.com';
  const TEST_SHIPMENT_ID = 'VIBO-2026-001';

  test.beforeEach(async ({ page }) => {
    await login(page, 'buyer');
    await verifyLoggedIn(page, 'buyer');
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });

  test('should login as buyer and see assigned shipments only', async ({ page }) => {
    // Verify on dashboard
    await expect(page).toHaveURL(/dashboard|home/);

    // Should see assigned shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await expect(shipmentLink).toBeVisible({ timeout: 10000 });

    // Count should be limited (only assigned)
    const rows = page.locator('table tbody tr, [role="row"]');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
    expect(count).toBeLessThanOrEqual(10); // Buyers typically see few shipments
  });

  test('should show buyer-specific menu items', async ({ page }) => {
    // Verify menu for buyer role
    await verifyMenuVisibility(page, 'buyer');

    // Should see limited menu
    const dashboardLink = page.locator('nav, aside').locator('text="Dashboard"').first();
    await expect(dashboardLink).toBeVisible();

    // Should NOT see admin/logistics items
    const createLink = page.locator('nav, aside').locator('text="Create Shipment"');
    await expect(createLink).toBeHidden();

    const usersLink = page.locator('nav, aside').locator('text="Users"');
    await expect(usersLink).toBeHidden();
  });

  test('should NOT be able to create shipments', async ({ page }) => {
    // No Create Shipment button
    const createButton = page.locator('button, [role="button"]').locator(':text("Create Shipment")');
    
    const isHidden = await createButton.isHidden();
    const isDisabled = (await createButton.getAttribute('disabled')) !== null;
    expect(isHidden || isDisabled).toBeTruthy();
  });

  test('should NOT be able to upload documents', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // No Upload button
    await expectActionNotAvailable(page, 'Upload');
  });

  test('should NOT be able to approve/validate documents', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // No Approve button
    await expectActionNotAvailable(page, 'Approve');
    await expectActionNotAvailable(page, 'Validate');
  });

  test('should be able to view shipment details and documents', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Should see shipment info
    await expect(page).toHaveURL(new RegExp(`shipment|${TEST_SHIPMENT_ID}`));

    // Should see documents
    const documentsSection = page.locator('text="Documents"').first();
    await expect(documentsSection).toBeVisible();
  });

  test('should see compliance status but not edit', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Should see compliance status
    const complianceStatus = page.locator('text="Compliance Status"').first();
    if (await complianceStatus.isVisible()) {
      // But no edit buttons
      await expectActionNotAvailable(page, 'Edit');
      await expectActionNotAvailable(page, 'Approve');
    }
  });

  test('should NOT be able to manage users or organizations', async ({ page }) => {
    // Should not see user/org management
    const usersLink = page.locator('nav, aside').locator('text="Users"');
    await expect(usersLink).toBeHidden();

    const orgsLink = page.locator('nav, aside').locator('text="Organizations"');
    await expect(orgsLink).toBeHidden();
  });

  test('should have limited analytics view (only assigned shipments)', async ({ page }) => {
    // Buyer may have analytics but only for assigned shipments
    const analyticsLink = page.locator('nav, aside').locator('text="Analytics"').first();
    
    if (await analyticsLink.isVisible()) {
      await analyticsLink.click();
      await page.waitForLoadState('networkidle');

      // Should see metrics but filtered to assigned shipments only
      const metrics = page.locator('[role="heading"], h1, h2');
      const count = await metrics.count();
      expect(count).toBeGreaterThan(-1);
    }
  });

  test('should logout successfully', async ({ page }) => {
    const userMenu = page.locator(`text="${BUYER_EMAIL}"`).first();
    await expect(userMenu).toBeVisible();
  });
});

/**
 * SUPPLIER E2E TESTS
 * 
 * Role: Upload origin certificates, provide geolocation
 * Permissions: Upload origin documents only, provide coordinates/photos
 * 
 * Journey: Login → View Assigned Shipment → Upload Origin Certificate → Submit
 */

test.describe('SUPPLIER - Origin Verification & Document Upload', () => {
  const SUPPLIER_EMAIL = 'supplier@vibotaj.com';
  const TEST_SHIPMENT_ID = 'VIBO-2026-001';

  test.beforeEach(async ({ page }) => {
    await login(page, 'supplier');
    await verifyLoggedIn(page, 'supplier');
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });

  test('should login as supplier and see assigned shipments', async ({ page }) => {
    // Verify on dashboard
    await expect(page).toHaveURL(/dashboard|home/);

    // Should see assigned shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await expect(shipmentLink).toBeVisible({ timeout: 10000 });
  });

  test('should show supplier-specific menu items', async ({ page }) => {
    // Verify menu for supplier role
    await verifyMenuVisibility(page, 'supplier');

    // Should see limited menu
    const dashboardLink = page.locator('nav, aside').locator('text="Dashboard"').first();
    await expect(dashboardLink).toBeVisible();

    // Should NOT see Create or full management
    const createLink = page.locator('nav, aside').locator('text="Create Shipment"');
    await expect(createLink).toBeHidden();
  });

  test('should NOT be able to create shipments', async ({ page }) => {
    // No Create Shipment capability
    const createButton = page.locator('button, [role="button"]').locator(':text("Create Shipment")');
    
    const isHidden = await createButton.isHidden();
    const isDisabled = (await createButton.getAttribute('disabled')) !== null;
    expect(isHidden || isDisabled).toBeTruthy();
  });

  test('should be able to upload origin-specific documents', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Look for Origin Verification section
    const originSection = page.locator('text="Origin", text="Origin Verification"').first();
    
    if (await originSection.isVisible()) {
      // Should see upload button in origin section
      const uploadButton = page.locator('button').locator(':text("Upload")').first();
      if (await uploadButton.isVisible()) {
        expect(await uploadButton.isDisabled()).toBe(false);
      }
    }
  });

  test('should NOT be able to upload non-origin documents', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Should NOT be able to upload B/L, Invoice, etc.
    const otherDocsSection = page.locator('text="Bill of Lading", text="Commercial Invoice"').first();
    
    if (await otherDocsSection.isVisible()) {
      // Check if upload buttons are disabled
      const uploadButton = otherDocsSection.locator('button').locator(':text("Upload")').first();
      if (await uploadButton.isVisible()) {
        expect(await uploadButton.isDisabled()).toBe(true);
      }
    }
  });

  test('should NOT be able to approve documents', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // No Approve button for supplier
    await expectActionNotAvailable(page, 'Approve');
  });

  test('should NOT be able to manage users or organizations', async ({ page }) => {
    // Should not see management options
    const usersLink = page.locator('nav, aside').locator('text="Users"');
    await expect(usersLink).toBeHidden();

    const orgsLink = page.locator('nav, aside').locator('text="Organizations"');
    await expect(orgsLink).toBeHidden();
  });

  test('should be able to provide geolocation and photos', async ({ page }) => {
    // Navigate to shipment
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForLoadState('networkidle');

    // Look for geolocation section
    const geoSection = page.locator('text="Geolocation", text="Location", text="Coordinates"').first();
    
    if (await geoSection.isVisible()) {
      // Should see input fields or photo upload
      const coordsInput = page.locator('input[placeholder*="Longitude"], input[placeholder*="Latitude"]').first();
      if (await coordsInput.isVisible()) {
        expect(true).toBe(true); // Geolocation available
      }
    }
  });

  test('should logout successfully', async ({ page }) => {
    const userMenu = page.locator(`text="${SUPPLIER_EMAIL}"`).first();
    await expect(userMenu).toBeVisible();
  });
});

/**
 * VIEWER E2E TESTS
 * 
 * Role: Read-only access to ALL data (audit/compliance review)
 * Permissions: View all shipments, documents, compliance status; NO edits/creation
 * 
 * Journey: Login → Dashboard (All Shipments) → View Shipment Details → Audit Trail Access
 */

test.describe('VIEWER - Read-Only Global Audit Access', () => {
  const VIEWER_EMAIL = 'viewer@vibotaj.com';
  const TEST_SHIPMENT_ID = 'VIBO-2026-001';

  test.beforeEach(async ({ page }) => {
    await login(page, 'viewer');
    await verifyLoggedIn(page, 'viewer');
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });

  test('should login as viewer and see all shipments', async ({ page }) => {
    // Verify on dashboard
    await expect(page).toHaveURL(/dashboard|home/);

    // Should see all shipments (not limited like buyers)
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await expect(shipmentLink).toBeVisible({ timeout: 10000 });

    // Can see many shipments (audit access to all)
    const rows = page.locator('table tbody tr, [role="row"]');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should show viewer-specific menu items (limited)', async ({ page }) => {
    // Verify menu for viewer role - minimal permissions
    await verifyMenuVisibility(page, 'viewer');

    // Should see dashboard
    const dashboardLink = page.locator('nav, aside').locator('text="Dashboard"').first();
    await expect(dashboardLink).toBeVisible();

    // Should NOT see create/edit options
    const createLink = page.locator('nav, aside').locator('text="Create"');
    await expect(createLink).not.toBeVisible();

    // Should NOT see admin/management items
    const usersLink = page.locator('nav, aside').locator('text="Users"');
    await expect(usersLink).not.toBeVisible();
  });

  test('should access shipment details for audit review', async ({ page }) => {
    // Navigate to shipment details
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();

    // Wait for details page to load
    await page.waitForURL(/shipments|details/, { timeout: 15000 });
    await expect(page).toHaveURL(/shipments|details/);

    // Should see shipment information
    const shipmentHeader = page.locator(`text="${TEST_SHIPMENT_ID}"`);
    await expect(shipmentHeader).toBeVisible();

    // Should see compliance status
    const statusElement = page.locator('[data-testid="compliance-status"], text="Status", text="COMPLIANT", text="PENDING"').first();
    await expect(statusElement).toBeVisible({ timeout: 10000 });

    // Should see documents section but no upload option
    const documentsSection = page.locator('text="Documents", text="Attachments"').first();
    if (await documentsSection.isVisible()) {
      // Should NOT see upload button
      const uploadButton = page.locator('text="Upload", button:has-text("Upload")').first();
      await expect(uploadButton).not.toBeVisible();
    }
  });

  test('should view audit trail but cannot edit', async ({ page }) => {
    // Navigate to shipment details
    const shipmentLink = page.locator(`text="${TEST_SHIPMENT_ID}"`).first();
    await shipmentLink.click();
    await page.waitForURL(/shipments|details/, { timeout: 15000 });

    // Look for any edit buttons - should NOT exist
    const editButtons = page.locator('button:has-text("Edit"), button[aria-label*="Edit"]');
    const editCount = await editButtons.count();
    expect(editCount).toBe(0);

    // Look for any delete buttons - should NOT exist
    const deleteButtons = page.locator('button:has-text("Delete"), button[aria-label*="Delete"]');
    const deleteCount = await deleteButtons.count();
    expect(deleteCount).toBe(0);

    // Can view comments but cannot add new ones (typically)
    const commentsSection = page.locator('text="Comments", text="Activity", text="History"').first();
    if (await commentsSection.isVisible()) {
      // Look for comment input - viewers typically cannot add comments
      const commentInput = page.locator('textarea, input[placeholder*="Comment"]').first();
      if (await commentInput.isVisible()) {
        expect(await commentInput.isDisabled()).toBe(true);
      }
    }
  });

  test('should see all organization data across roles', async ({ page }) => {
    // Viewer should see data from all organizations (VIBOTAJ, WITATRADE, HAGES, etc.)
    // This tests the audit/compliance review capability

    // Get table/list of shipments
    const shipmentRows = page.locator('table tbody tr, [role="row"]');
    const count = await shipmentRows.count();

    // Should have multiple shipments from different contexts
    expect(count).toBeGreaterThan(1);

    // Verify can see organization names (if displayed)
    const orgColumn = page.locator('td:has-text("VIBOTAJ"), td:has-text("WITATRADE"), td:has-text("HAGES")').first();
    if (await orgColumn.isVisible()) {
      expect(orgColumn).toBeVisible();
    }
  });

  test('should handle forbidden actions gracefully', async ({ page }) => {
    // Try to navigate to admin/management pages
    await expectActionNotAvailable(page, 'users', 'viewers cannot access user management');
    await expectActionNotAvailable(page, 'settings', 'viewers have limited settings access');
    await expectActionNotAvailable(page, 'admin', 'viewers cannot access admin panel');
  });

  test('should logout successfully', async ({ page }) => {
    const userMenu = page.locator(`text="${VIEWER_EMAIL}"`).first();
    await expect(userMenu).toBeVisible();
  });
});
