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
    email: '31stcenturyglobalventures@gmail.com',
    password: 'Adeshola123!',
    role: 'logistics',
    organization: 'VIBOTAJ',
    displayName: 'Logistics Agent',
  },
  buyer: {
    email: 'buyer@vibotaj.com',
    password: 'tracehub2026',
    role: 'buyer',
    organization: 'VIBOTAJ',
    displayName: 'Buyer',
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
    displayName: 'Viewer/Auditor',
  },
};

/**
 * Clear browser session/storage to ensure clean state
 */
export async function clearSession(page: Page) {
  // Clear localStorage and sessionStorage
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  // Clear cookies
  await page.context().clearCookies();
}

/**
 * Ensure user is logged out before test
 */
export async function ensureLoggedOut(page: Page) {
  await clearSession(page);
  await page.goto('/login');
  await page.waitForLoadState('domcontentloaded');
}

/**
 * Login to TraceHub
 */
export async function login(page: Page, role: UserRole) {
  const user = TEST_USERS[role];

  // Clear any existing session first
  await clearSession(page);

  // Navigate to login page directly
  await page.goto('/login');
  await page.waitForLoadState('domcontentloaded');

  // Wait a bit for React to render
  await page.waitForTimeout(2000);

  // Check if already on dashboard (somehow still logged in)
  const currentUrl = page.url();
  if (currentUrl.includes('/dashboard')) {
    // Already logged in - clear session and try again
    await clearSession(page);
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);
  }

  // Wait for login form to appear - username field (not email)
  const usernameInput = page.locator('input[id="username"], input[placeholder*="username"], input[placeholder*="Username"], input[name="username"], input[type="email"]');
  await usernameInput.waitFor({ state: 'visible', timeout: 10000 });

  // Fill login credentials - use email as username
  await usernameInput.fill(user.email);
  
  const passwordInput = page.locator('input[type="password"], input[placeholder*="Password"], input[placeholder*="password"]');
  await passwordInput.fill(user.password);

  // Submit login - look for Submit button
  const loginButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In"), button:has-text("login")');
  await loginButton.click();

  // Wait for redirect to dashboard
  await page.waitForURL('**/dashboard', { timeout: 15000 });
  await page.waitForLoadState('networkidle');

  // Verify logged in (check for logout button or user menu)
  const userMenu = page.locator('[aria-label*="User"], [aria-label*="Profile"], [role="button"]:has-text("' + user.email + '")');
  await expect(userMenu).toBeVisible({ timeout: 5000 });
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
  
  // Verify user info visible somewhere
  const userIndicator = page.locator('text=' + user.email).first();
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
 */
export async function verifyMenuVisibility(page: Page, role: UserRole) {
  const menuRules: Record<UserRole, { visible: string[]; hidden?: string[] }> = {
    admin: {
      visible: ['Dashboard', 'Shipments', 'Users', 'Organizations', 'Analytics', 'Settings'],
    },
    compliance: {
      visible: ['Dashboard', 'Shipments', 'Documents', 'Analytics'],
      hidden: ['Users', 'Organizations', 'Settings'],
    },
    logistics: {
      visible: ['Dashboard', 'Shipments', 'Create Shipment', 'My Documents'],
      hidden: ['Users', 'Organizations', 'Analytics'],
    },
    buyer: {
      visible: ['Dashboard', 'My Shipments', 'Analytics'],
      hidden: ['Create Shipment', 'Users', 'Organizations', 'Settings'],
    },
    supplier: {
      visible: ['Dashboard', 'My Shipments', 'Upload Documents'],
      hidden: ['Create Shipment', 'Users', 'Organizations', 'Settings'],
    },
    viewer: {
      visible: ['Dashboard', 'Analytics', 'Reports'],
      hidden: ['Create Shipment', 'Users', 'Organizations', 'Settings'],
    },
  };

  const rule = menuRules[role];

  // Check visible items
  for (const item of rule.visible) {
    const menuItem = page.locator(`nav >> text="${item}", aside >> text="${item}"`).first();
    await expect(menuItem).toBeVisible({ timeout: 5000 });
  }

  // Check hidden items
  if (rule.hidden) {
    for (const item of rule.hidden) {
      const menuItem = page.locator(`nav >> text="${item}", aside >> text="${item}"`).first();
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
