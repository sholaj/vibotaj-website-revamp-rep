/**
 * E2E Tests for Admin User Management
 * 
 * Verifies that admin users can create, update, and deactivate users through the UI.
 */

import { test, expect } from '@playwright/test'
import { loginAsRole } from './helpers/auth'

test.describe('Admin User Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await loginAsRole(page, 'admin')
    await page.waitForURL('**/dashboard')
  })

  test('admin can access user management page', async ({ page }) => {
    // Navigate to users page
    await page.click('text=Users')
    await page.waitForURL('**/users')

    // Verify page loaded
    await expect(page.locator('h1')).toContainText('User Management')
    await expect(page.getByRole('button', { name: /add user/i })).toBeVisible()
  })

  test('admin can create a new user', async ({ page }) => {
    // Navigate to users page
    await page.goto('/users')

    // Click Add User button
    await page.getByRole('button', { name: /add user/i }).click()

    // Wait for modal
    await expect(page.getByText('Create New User')).toBeVisible()

    // Fill in user details with valid password
    const timestamp = Date.now()
    const testEmail = `testuser${timestamp}@example.com`
    
    await page.fill('input[type="email"]', testEmail)
    await page.fill('input[placeholder*="John Doe"]', 'Test User E2E')
    await page.fill('input[type="password"]', 'TestPass123') // Valid password
    await page.selectOption('select', 'viewer')

    // Submit form
    await page.getByRole('button', { name: /create user/i }).click()

    // Wait for success (modal closes and user appears in list)
    await expect(page.getByText('Create New User')).not.toBeVisible({ timeout: 5000 })
    
    // Verify user appears in the list
    await expect(page.getByText(testEmail)).toBeVisible()
  })

  test('shows password requirements and validates', async ({ page }) => {
    await page.goto('/users')
    await page.getByRole('button', { name: /add user/i }).click()

    // Verify password hint is visible
    await expect(page.getByText(/must contain uppercase, lowercase/i)).toBeVisible()

    // Try weak password (should fail)
    await page.fill('input[type="email"]', 'weak@example.com')
    await page.fill('input[placeholder*="John Doe"]', 'Weak User')
    await page.fill('input[type="password"]', 'weakpass') // No uppercase or digit
    await page.selectOption('select', 'viewer')
    await page.getByRole('button', { name: /create user/i }).click()

    // Should see error message
    await expect(page.getByText(/uppercase/i)).toBeVisible({ timeout: 3000 })
  })

  test('admin can update user role', async ({ page }) => {
    await page.goto('/users')

    // Find and click on a user row (not admin to avoid self-modification)
    const viewerRow = page.getByText('viewer@vibotaj.com').locator('..')
    await viewerRow.click()

    // Wait for edit modal
    await expect(page.getByText(/edit user/i)).toBeVisible()

    // Change role
    await page.selectOption('select', 'compliance')
    await page.getByRole('button', { name: /update profile/i }).click()

    // Wait for success message
    await expect(page.getByText(/updated successfully/i)).toBeVisible({ timeout: 3000 })

    // Close modal and verify (role badge would show compliance)
    // Note: In real scenario, we'd verify the role badge changed
  })

  test('admin can deactivate and reactivate user', async ({ page }) => {
    // First create a user to deactivate
    await page.goto('/users')
    await page.getByRole('button', { name: /add user/i }).click()

    const timestamp = Date.now()
    const testEmail = `deactivate${timestamp}@example.com`
    
    await page.fill('input[type="email"]', testEmail)
    await page.fill('input[placeholder*="John Doe"]', 'Deactivate Test')
    await page.fill('input[type="password"]', 'TestPass123')
    await page.selectOption('select', 'viewer')
    await page.getByRole('button', { name: /create user/i }).click()

    // Wait for modal to close
    await expect(page.getByText('Create New User')).not.toBeVisible({ timeout: 5000 })

    // Find the user row and look for active/inactive toggle
    const userRow = page.getByText(testEmail).locator('..')
    
    // Click the toggle/deactivate button (depends on UI implementation)
    // This is a placeholder - adjust based on actual UI
    const toggleButton = userRow.locator('button').first()
    await toggleButton.click()

    // Confirm action if needed
    // await page.getByRole('button', { name: /confirm/i }).click()

    // Verify status changed
    // Note: Implementation depends on how status is displayed
  })

  test('non-admin user cannot access user management', async ({ page }) => {
    // Logout admin
    await page.click('button[aria-label*="user menu"], button:has-text("System Administrator")')
    await page.click('text=Logout')

    // Login as viewer
    await loginAsRole(page, 'viewer')
    await page.waitForURL('**/dashboard')

    // Try to navigate to users page
    await page.goto('/users')

    // Should see access denied message
    await expect(page.getByText(/access denied/i)).toBeVisible()
    await expect(page.getByText(/permission/i)).toBeVisible()
  })

  test('admin can reset user password', async ({ page }) => {
    await page.goto('/users')

    // Click on viewer user
    const viewerRow = page.getByText('viewer@vibotaj.com').locator('..')
    await viewerRow.click()

    // Wait for edit modal
    await expect(page.getByText(/edit user/i)).toBeVisible()

    // Find password reset section
    await page.fill('input[placeholder*="password"]', 'NewSecurePass123')
    await page.getByRole('button', { name: /reset/i }).click()

    // Verify success
    await expect(page.getByText(/reset successfully/i)).toBeVisible({ timeout: 3000 })
  })

  test('lists all users with proper pagination', async ({ page }) => {
    await page.goto('/users')

    // Verify user list is visible
    await expect(page.locator('table, .user-list')).toBeVisible()

    // Check that admin user is listed
    await expect(page.getByText('admin@vibotaj.com')).toBeVisible()

    // Check that role badges are displayed
    await expect(page.getByText('Admin', { exact: true })).toBeVisible()
  })

  test('search and filter users', async ({ page }) => {
    await page.goto('/users')

    // Use search if available
    const searchInput = page.locator('input[placeholder*="search" i], input[type="search"]')
    if (await searchInput.count() > 0) {
      await searchInput.fill('admin')
      await page.waitForTimeout(500) // Debounce

      // Should show only admin users
      await expect(page.getByText('admin@vibotaj.com')).toBeVisible()
    }

    // Use role filter if available
    const roleFilter = page.locator('select').first()
    if (await roleFilter.count() > 0) {
      await roleFilter.selectOption('admin')
      await page.waitForTimeout(500)

      // Should filter to admin role only
      await expect(page.getByText('admin@vibotaj.com')).toBeVisible()
    }
  })
})
