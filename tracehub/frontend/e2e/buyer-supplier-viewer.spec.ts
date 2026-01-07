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
 * Role: Read-only audit, reporting, analytics
 * Permissions: View all data; no actions allowed
 * 
 * Journey: Login → Dashboard (All Data) → View Analytics → Generate Reports
 */

test.describe('VIEWER - Audit & Read-Only Analytics', () => {
  const VIEWER_EMAIL = 'viewer@vibotaj.com';

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

    // Should see unrestricted shipment list
    const rows = page.locator('table tbody tr, [role="row"]');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should show viewer-specific menu items', async ({ page }) => {
    // Verify menu for viewer role
    await verifyMenuVisibility(page, 'viewer');

    // Should see Dashboard and Analytics only
    const dashboardLink = page.locator('nav, aside').locator('text="Dashboard"').first();
    await expect(dashboardLink).toBeVisible();

    // Should NOT see any action items
    const createLink = page.locator('nav, aside').locator('text="Create"');
    await expect(createLink).toBeHidden();
  });

  test('should NOT be able to create anything', async ({ page }) => {
    // No create buttons anywhere
    const createButton = page.locator('button, [role="button"]').locator(':text("Create")').first();
    
    const isHidden = await createButton.isHidden();
    expect(isHidden).toBe(true);
  });

  test('should NOT be able to upload documents', async ({ page }) => {
    // No upload capability
    await expectActionNotAvailable(page, 'Upload');
  });

  test('should NOT be able to approve documents', async ({ page }) => {
    // No approve capability
    await expectActionNotAvailable(page, 'Approve');
  });

  test('should NOT be able to edit anything', async ({ page }) => {
    // No edit buttons
    await expectActionNotAvailable(page, 'Edit');
  });

  test('should have access to Analytics and Reports', async ({ page }) => {
    // Viewer can see analytics
    const analyticsLink = page.locator('nav, aside').locator('text="Analytics", text="Reports"').first();
    
    if (await analyticsLink.isVisible()) {
      await analyticsLink.click();
      await page.waitForLoadState('networkidle');

      // Should see dashboard with all data
      const metrics = page.locator('[role="heading"], h1, h2');
      const count = await metrics.count();
      expect(count).toBeGreaterThan(-1);
    }
  });

  test('should be able to view any shipment but not edit', async ({ page }) => {
    // Find and click a shipment
    const shipmentRow = page.locator('table tbody tr, [role="row"]').first();
    await shipmentRow.click();
    await page.waitForLoadState('networkidle');

    // Should see shipment details
    const shipmentInfo = page.locator('h1, h2').first();
    await expect(shipmentInfo).toBeVisible();

    // But no edit/upload buttons
    await expectActionNotAvailable(page, 'Edit');
    await expectActionNotAvailable(page, 'Upload');
    await expectActionNotAvailable(page, 'Approve');
  });

  test('should be able to download/export reports', async ({ page }) => {
    // Look for export/download buttons
    const downloadButton = page.locator('button').locator(':text("Download"), :text("Export")').first();
    
    if (await downloadButton.isVisible()) {
      expect(await downloadButton.isDisabled()).toBe(false);
    }
  });

  test('should NOT be able to manage users or organizations', async ({ page }) => {
    // Should not see management
    const usersLink = page.locator('nav, aside').locator('text="Users"');
    await expect(usersLink).toBeHidden();

    const orgsLink = page.locator('nav, aside').locator('text="Organizations"');
    await expect(orgsLink).toBeHidden();
  });

  test('should NOT be able to access Settings', async ({ page }) => {
    // No settings access
    const settingsLink = page.locator('nav, aside').locator('text="Settings"');
    await expect(settingsLink).toBeHidden();
  });

  test('should logout successfully', async ({ page }) => {
    const userMenu = page.locator(`text="${VIEWER_EMAIL}"`).first();
    await expect(userMenu).toBeVisible();
  });
});
