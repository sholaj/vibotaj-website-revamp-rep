import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth, Permission } from '../AuthContext'
import type { CurrentUser } from '../../types'
import api from '../../api/client'

// Mock the API client
vi.mock('../../api/client', () => ({
  default: {
    isAuthenticated: vi.fn(),
    verifyToken: vi.fn(),
    getCurrentUserFull: vi.fn(),
    logout: vi.fn(),
    login: vi.fn()
  }
}))

// Test component that uses the auth context
function TestComponent() {
  const auth = useAuth()
  
  return (
    <div>
      <div data-testid="authenticated">{auth.isAuthenticated ? 'yes' : 'no'}</div>
      <div data-testid="loading">{auth.isLoading ? 'yes' : 'no'}</div>
      <div data-testid="user">{auth.user?.email || 'none'}</div>
      <div data-testid="role">{auth.user?.role || 'none'}</div>
      <div data-testid="is-admin">{auth.isAdmin ? 'yes' : 'no'}</div>
      <div data-testid="is-compliance">{auth.isCompliance ? 'yes' : 'no'}</div>
      <div data-testid="can-manage-users">{auth.canManageUsers ? 'yes' : 'no'}</div>
      <div data-testid="can-validate-docs">{auth.canValidateDocuments ? 'yes' : 'no'}</div>
      <button onClick={() => auth.login('test-token')}>Login</button>
      <button onClick={auth.logout}>Logout</button>
      <button onClick={auth.refreshUser}>Refresh</button>
    </div>
  )
}

describe('AuthContext', () => {
  const mockAdminUser: CurrentUser = {
    id: 'user-1',
    email: 'admin@example.com',
    full_name: 'Admin User',
    role: 'admin',
    is_active: true,
    organization_id: 'org-1',
    permissions: [
      Permission.USERS_CREATE,
      Permission.USERS_READ,
      Permission.USERS_UPDATE,
      Permission.USERS_DELETE,
      Permission.DOCUMENTS_VALIDATE,
      Permission.DOCUMENTS_UPLOAD,
      Permission.SYSTEM_ADMIN
    ]
  }

  const mockComplianceUser: CurrentUser = {
    id: 'user-2',
    email: 'compliance@example.com',
    full_name: 'Compliance User',
    role: 'compliance',
    is_active: true,
    organization_id: 'org-1',
    permissions: [
      Permission.DOCUMENTS_VALIDATE,
      Permission.DOCUMENTS_APPROVE,
      Permission.DOCUMENTS_REJECT,
      Permission.SHIPMENTS_READ
    ]
  }

  const mockBuyerUser: CurrentUser = {
    id: 'user-3',
    email: 'buyer@example.com',
    full_name: 'Buyer User',
    role: 'buyer',
    is_active: true,
    organization_id: 'org-1',
    permissions: [
      Permission.SHIPMENTS_CREATE,
      Permission.DOCUMENTS_UPLOAD,
      Permission.DOCUMENTS_READ
    ]
  }

  beforeEach(() => {
    vi.clearAllMocks()
    // Default: not authenticated
    vi.mocked(api.isAuthenticated).mockReturnValue(false)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initial State', () => {
    it('should start with no user when not authenticated', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('no')
      })

      expect(screen.getByTestId('authenticated')).toHaveTextContent('no')
      expect(screen.getByTestId('user')).toHaveTextContent('none')
    })

    it('should fetch user details when authenticated', async () => {
      vi.mocked(api.isAuthenticated).mockReturnValue(true)
      vi.mocked(api.verifyToken).mockResolvedValue(true)
      vi.mocked(api.getCurrentUserFull).mockResolvedValue(mockAdminUser)

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('yes')
      })

      expect(screen.getByTestId('user')).toHaveTextContent('admin@example.com')
      expect(screen.getByTestId('role')).toHaveTextContent('admin')
    })

    it('should logout when token verification fails', async () => {
      vi.mocked(api.isAuthenticated).mockReturnValue(true)
      vi.mocked(api.verifyToken).mockResolvedValue(false)

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('no')
      })

      expect(api.logout).toHaveBeenCalled()
      expect(screen.getByTestId('authenticated')).toHaveTextContent('no')
    })
  })

  describe('Role-Based Access', () => {
    it('should identify admin role', async () => {
      vi.mocked(api.isAuthenticated).mockReturnValue(true)
      vi.mocked(api.verifyToken).mockResolvedValue(true)
      vi.mocked(api.getCurrentUserFull).mockResolvedValue(mockAdminUser)

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('is-admin')).toHaveTextContent('yes')
      })

      expect(screen.getByTestId('is-compliance')).toHaveTextContent('no')
    })

    it('should identify compliance role', async () => {
      vi.mocked(api.isAuthenticated).mockReturnValue(true)
      vi.mocked(api.verifyToken).mockResolvedValue(true)
      vi.mocked(api.getCurrentUserFull).mockResolvedValue(mockComplianceUser)

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('is-compliance')).toHaveTextContent('yes')
      })

      expect(screen.getByTestId('is-admin')).toHaveTextContent('no')
    })

    it('should identify buyer role', async () => {
      vi.mocked(api.isAuthenticated).mockReturnValue(true)
      vi.mocked(api.verifyToken).mockResolvedValue(true)
      vi.mocked(api.getCurrentUserFull).mockResolvedValue(mockBuyerUser)

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('role')).toHaveTextContent('buyer')
      })
    })
  })

  describe('Permission Checks', () => {
    it('should correctly check admin permissions', async () => {
      vi.mocked(api.isAuthenticated).mockReturnValue(true)
      vi.mocked(api.verifyToken).mockResolvedValue(true)
      vi.mocked(api.getCurrentUserFull).mockResolvedValue(mockAdminUser)

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('can-manage-users')).toHaveTextContent('yes')
      })

      expect(screen.getByTestId('can-validate-docs')).toHaveTextContent('yes')
    })

    it('should correctly check compliance permissions', async () => {
      vi.mocked(api.isAuthenticated).mockReturnValue(true)
      vi.mocked(api.verifyToken).mockResolvedValue(true)
      vi.mocked(api.getCurrentUserFull).mockResolvedValue(mockComplianceUser)

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('can-validate-docs')).toHaveTextContent('yes')
      })

      expect(screen.getByTestId('can-manage-users')).toHaveTextContent('no')
    })

    it('should deny permissions when not authenticated', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('no')
      })

      expect(screen.getByTestId('can-manage-users')).toHaveTextContent('no')
      expect(screen.getByTestId('can-validate-docs')).toHaveTextContent('no')
    })
  })

  describe('Login/Logout', () => {
    it('should handle logout', async () => {
      vi.mocked(api.isAuthenticated).mockReturnValue(true)
      vi.mocked(api.verifyToken).mockResolvedValue(true)
      vi.mocked(api.getCurrentUserFull).mockResolvedValue(mockAdminUser)

      const { getByText } = render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('yes')
      })

      const logoutButton = getByText('Logout')
      logoutButton.click()

      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('no')
      })

      expect(api.logout).toHaveBeenCalled()
      expect(screen.getByTestId('user')).toHaveTextContent('none')
    })

    it('should handle login', async () => {
      vi.mocked(api.getCurrentUserFull).mockResolvedValue(mockAdminUser)

      const { getByText } = render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('no')
      })

      const loginButton = getByText('Login')
      loginButton.click()

      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('yes')
      })

      expect(screen.getByTestId('user')).toHaveTextContent('admin@example.com')
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors during verification', async () => {
      vi.mocked(api.isAuthenticated).mockReturnValue(true)
      vi.mocked(api.verifyToken).mockRejectedValue(new Error('Network error'))

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('no')
      })

      expect(consoleSpy).toHaveBeenCalled()
      expect(api.logout).toHaveBeenCalled()

      consoleSpy.mockRestore()
    })

    it('should handle user fetch errors', async () => {
      vi.mocked(api.isAuthenticated).mockReturnValue(true)
      vi.mocked(api.verifyToken).mockResolvedValue(true)
      vi.mocked(api.getCurrentUserFull).mockRejectedValue(new Error('Fetch failed'))

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('no')
      })

      expect(screen.getByTestId('authenticated')).toHaveTextContent('no')

      consoleSpy.mockRestore()
    })
  })

  describe('useAuth Hook', () => {
    it('should throw error when used outside provider', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      expect(() => {
        render(<TestComponent />)
      }).toThrow('useAuth must be used within an AuthProvider')

      consoleSpy.mockRestore()
    })
  })

  describe('Permission Constants', () => {
    it('should have correct permission values', () => {
      expect(Permission.USERS_CREATE).toBe('users:create')
      expect(Permission.DOCUMENTS_VALIDATE).toBe('documents:validate')
      expect(Permission.SHIPMENTS_READ).toBe('shipments:read')
      expect(Permission.SYSTEM_ADMIN).toBe('system:admin')
    })
  })
})
