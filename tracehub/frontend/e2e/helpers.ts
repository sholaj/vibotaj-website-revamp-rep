import { Page, expect } from '@playwright/test';

/**
 * Auth Helper: Login functions for all 6 user roles
 */

export type UserRole = 'admin' | 'compliance' | 'logistics' | 'buyer' | 'supplier' | 'viewer';

export interface TestUser {
  email: string;
  password: string;
  role: UserRole;
  organization: string;
  displayName?: string;
}

export const TEST_USERS: Record<UserRole, TestUser> = {
  admin: {
    email: 'admin@vibotaj.com',
    password: 'tracehub2026',
    role: 'admin',
    organization: 'VIBOTAJ',
    displayName: 'Admin User',
  },
  compliance: {
    email: 'compliance@vibotaj.com',
    password: 'tracehub2026',
    role: 'compliance',
    organization: 'VIBOTAJ',
    displayName: 'Compliance Officer',
  },
  logistics: {
    email: 'logistic@vibotaj.com',
    password: 'tracehub2026',
    role: 'logistics',
    organization: 'VIBOTAJ',
    displayName: 'Logistics Manager',
  },
  buyer: {
    email: 'buyer@witatrade.de',
    password: 'tracehub2026',
    role: 'buyer',
    organization: 'WITATRADE',
    displayName: 'Hans Mueller',
  },
  supplier: {
    email: 'supplier@vibotaj.com',
    password: 'tracehub2026',
    role: 'supplier',
    organization: 'VIBOTAJ',
    displayName: 'Supplier',
  },
  viewer: {
    email: 'viewer@vibotaj.com',
    password: 'tracehub2026',
    role: 'viewer',
    organization: 'VIBOTAJ',
    displayName: 'Audit Viewer',
  },
};

/**
 * Login to TraceHub
 */
export async function login(page: Page, role: UserRole) {
  const user = TEST_USERS[role];
  
  // Navigate to login page directly
  await page.goto('/login');
  await page.waitForLoadState('domcontentloaded');
  
  // Wait a bit for React to render
  await page.waitForTimeout(2000);

  // Wait for login form to appear - use username field (not email)
  const usernameInput = page.locator('input[id="username"]');
  await usernameInput.waitFor({ state: 'visible', timeout: 10000 });

  // Fill login credentials
  await usernameInput.fill(user.email);
  
  const passwordInput = page.locator('input[type="password"], input[placeholder*="Password"], input[placeholder*="password"]');
  await passwordInput.fill(user.password);

  // Submit login - the button text is "Sign in" not "Login"
  const loginButton = page.locator('button[type="submit"]');
  await loginButton.click();
  
  // Wait for navigation away from login page
  await page.waitForURL(url => !url.toString().includes('/login'), { timeout: 15000 });
  await page.waitForLoadState('networkidle');
}

/**
 * Logout from TraceHub
 */
export async function logout(page: Page) {
  // Find and click logout button (varies by role/org)
  const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign out"), [role="menuitem"]:has-text("Logout")');
  
  if (await logoutButton.isVisible()) {
    await logoutButton.click();
  } else {
    // Try user menu → logout
    const userMenu = page.locator('[aria-label*="User"], [aria-label*="Profile"]').first();
    if (await userMenu.isVisible()) {
      await userMenu.click();
      await page.locator('text="Logout"').click();
    }
  }

  // Verify redirected to login
  await page.waitForURL('**/login', { timeout: 10000 });
}

/**
 * Verify user is logged in
 */
export async function verifyLoggedIn(page: Page, role: UserRole) {
  const user = TEST_USERS[role];

  // Check for dashboard or welcome element
  await expect(page).toHaveURL(/dashboard|home/);

  // Verify user info visible in footer (format: "Logged in as {email}")
  const userIndicator = page.locator(`text=Logged in as ${user.email}`);
  await expect(userIndicator).toBeVisible({ timeout: 5000 });
}

/**
 * Get current logged-in user role from UI
 * (reads from role-specific menu or header)
 */
export async function getCurrentUserRole(page: Page): Promise<string | null> {
  try {
    const roleIndicator = page.locator('[aria-label*="Role"], [data-role], .role-badge');
    const text = await roleIndicator.textContent();
    return text?.toLowerCase() || null;
  } catch {
    return null;
  }
}

/**
 * Verify button/action is VISIBLE (allowed)
 */
export async function expectActionAvailable(page: Page, buttonLabel: string) {
  const button = page.locator(`button:has-text("${buttonLabel}"), [role="button"]:has-text("${buttonLabel}")`).first();
  await expect(button).toBeVisible({ timeout: 5000 });
  await expect(button).not.toBeDisabled();
}

/**
 * Verify button/action is HIDDEN or DISABLED (not allowed)
 */
export async function expectActionNotAvailable(page: Page, buttonLabel: string) {
  const button = page.locator(`button:has-text("${buttonLabel}"), [role="button"]:has-text("${buttonLabel}")`).first();
  
  // Check if hidden OR disabled
  const isHidden = await button.isHidden();
  const isDisabled = (await button.getAttribute('disabled')) !== null;
  
  expect(isHidden || isDisabled).toBeTruthy();
}

/**
 * Navigate to section (dashboard, shipments, documents, etc.)
 */
export async function navigateTo(page: Page, section: string) {
  const sectionLink = page.locator(`[role="navigation"] >> text="${section}", aside >> text="${section}", nav >> text="${section}"`).first();
  await sectionLink.click();
  await page.waitForLoadState('networkidle');
}

/**
 * Verify menu items visible for role
 *
 * Actual UI navigation (from Layout.tsx):
 * - Dashboard: visible to all
 * - Analytics: visible to all
 * - Users: visible only to admin (canManageUsers permission)
 * - Logout: always visible
 */
export async function verifyMenuVisibility(page: Page, role: UserRole) {
  const menuRules: Record<UserRole, { visible: string[]; hidden?: string[] }> = {
    admin: {
      visible: ['Dashboard', 'Analytics', 'Users'],
    },
    compliance: {
      visible: ['Dashboard', 'Analytics'],
      hidden: ['Users'],
    },
    logistics: {
      visible: ['Dashboard', 'Analytics'],
      hidden: ['Users'],
    },
    buyer: {
      visible: ['Dashboard', 'Analytics'],
      hidden: ['Users'],
    },
    supplier: {
      visible: ['Dashboard', 'Analytics'],
      hidden: ['Users'],
    },
    viewer: {
      visible: ['Dashboard', 'Analytics'],
      hidden: ['Users'],
    },
  };

  const rule = menuRules[role];

  // Check visible items in nav
  for (const item of rule.visible) {
    const menuItem = page.locator(`nav a:has-text("${item}")`).first();
    await expect(menuItem).toBeVisible({ timeout: 5000 });
  }

  // Check hidden items
  if (rule.hidden) {
    for (const item of rule.hidden) {
      const menuItem = page.locator(`nav a:has-text("${item}")`).first();
      await expect(menuItem).toBeHidden();
    }
  }
}

/**
 * Verify shipment is visible/hidden in dashboard
 */
export async function expectShipmentVisible(page: Page, shipmentId: string) {
  const shipmentRow = page.locator(`text="${shipmentId}"`).first();
  await expect(shipmentRow).toBeVisible({ timeout: 5000 });
}

export async function expectShipmentHidden(page: Page, shipmentId: string) {
  const shipmentRow = page.locator(`text="${shipmentId}"`);
  await expect(shipmentRow).toBeHidden();
}

/**
 * Get shipment count from dashboard
 */
export async function getShipmentCount(page: Page): Promise<number> {
  // This depends on actual UI structure - adjust based on actual dashboard
  const rows = page.locator('table tbody tr, [role="row"]');
  return await rows.count();
}

/**
 * Verify no console errors
 */
export async function verifyNoConsoleErrors(page: Page): Promise<string[]> {
  const errors: string[] = [];
  
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  return errors;
}

/**
 * Wait for element with retry
 */
export async function waitForElement(page: Page, selector: string, timeout = 10000) {
  await page.waitForSelector(selector, { timeout });
  const element = page.locator(selector).first();
  await expect(element).toBeVisible();
  return element;
}
