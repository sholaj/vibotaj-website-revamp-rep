import { Outlet, Link, useLocation } from 'react-router-dom'
import { Package, LogOut, Home, BarChart3, Users, Shield } from 'lucide-react'
import NotificationBell from './NotificationBell'
import { useAuth } from '../contexts/AuthContext'
import type { UserRole } from '../types'

interface LayoutProps {
  onLogout: () => void
}

// Role badge styling
const roleBadgeStyles: Record<UserRole, string> = {
  admin: 'bg-purple-100 text-purple-800',
  compliance: 'bg-blue-100 text-blue-800',
  logistics_agent: 'bg-teal-100 text-teal-800',
  buyer: 'bg-green-100 text-green-800',
  supplier: 'bg-orange-100 text-orange-800',
  viewer: 'bg-gray-100 text-gray-800',
}

const roleLabels: Record<UserRole, string> = {
  admin: 'Admin',
  compliance: 'Compliance',
  logistics_agent: 'Logistics Agent',
  buyer: 'Buyer',
  supplier: 'Supplier',
  viewer: 'Viewer',
}

export default function Layout({ onLogout }: LayoutProps) {
  const location = useLocation()
  const { user, isAdmin, canManageUsers } = useAuth()

  // Base navigation items
  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: Home, show: true },
    { name: 'Analytics', href: '/analytics', icon: BarChart3, show: true },
    // Admin-only items
    { name: 'Users', href: '/users', icon: Users, show: canManageUsers },
  ].filter(item => item.show)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <Package className="h-8 w-8 text-primary-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">TraceHub</span>
            </div>

            {/* Navigation */}
            <nav className="flex items-center space-x-4">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {item.name}
                  </Link>
                )
              })}

              {/* Notification Bell */}
              <NotificationBell />

              {/* Divider */}
              <div className="h-6 w-px bg-gray-200" />

              {/* User Info & Role Badge */}
              {user && (
                <div className="flex items-center space-x-2">
                  <div className="text-right hidden sm:block">
                    <p className="text-sm font-medium text-gray-900 truncate max-w-[120px]">
                      {user.full_name}
                    </p>
                    <div className="flex items-center justify-end">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${roleBadgeStyles[user.role]}`}>
                        {isAdmin && <Shield className="h-3 w-3 mr-1" />}
                        {roleLabels[user.role]}
                      </span>
                    </div>
                  </div>

                  {/* Mobile: Show just the badge */}
                  <div className="sm:hidden">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${roleBadgeStyles[user.role]}`}>
                      {isAdmin && <Shield className="h-3 w-3 mr-1" />}
                      {roleLabels[user.role]}
                    </span>
                  </div>
                </div>
              )}

              {/* Divider */}
              <div className="h-6 w-px bg-gray-200" />

              <button
                onClick={onLogout}
                className="flex items-center px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors"
              >
                <LogOut className="h-4 w-4 mr-2" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-500">
              TraceHub - Container Tracking & Compliance Platform
            </p>
            {user && (
              <p className="text-xs text-gray-400">
                Logged in as {user.email}
              </p>
            )}
          </div>
        </div>
      </footer>
    </div>
  )
}
