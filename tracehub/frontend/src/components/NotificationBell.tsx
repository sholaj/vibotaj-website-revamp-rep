/**
 * NotificationBell Component
 *
 * Displays a bell icon with unread notification count badge.
 * Clicking opens a dropdown with recent notifications.
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Bell,
  X,
  Check,
  CheckCheck,
  FileText,
  FileCheck,
  FileX,
  Clock,
  Anchor,
  Ship,
  Package,
  AlertTriangle,
  Calendar,
  Info,
} from 'lucide-react'
import api from '../api/client'
import type { Notification, NotificationType } from '../types'

// Map notification types to icons and colors
const NOTIFICATION_CONFIG: Record<
  NotificationType,
  { icon: React.ComponentType<{ className?: string }>; color: string; bgColor: string }
> = {
  document_uploaded: { icon: FileText, color: 'text-blue-600', bgColor: 'bg-blue-100' },
  document_validated: { icon: FileCheck, color: 'text-green-600', bgColor: 'bg-green-100' },
  document_rejected: { icon: FileX, color: 'text-red-600', bgColor: 'bg-red-100' },
  eta_changed: { icon: Clock, color: 'text-yellow-600', bgColor: 'bg-yellow-100' },
  shipment_arrived: { icon: Anchor, color: 'text-green-600', bgColor: 'bg-green-100' },
  shipment_departed: { icon: Ship, color: 'text-blue-600', bgColor: 'bg-blue-100' },
  shipment_delivered: { icon: Package, color: 'text-green-600', bgColor: 'bg-green-100' },
  compliance_alert: { icon: AlertTriangle, color: 'text-orange-600', bgColor: 'bg-orange-100' },
  expiry_warning: { icon: Calendar, color: 'text-yellow-600', bgColor: 'bg-yellow-100' },
  system_alert: { icon: Info, color: 'text-gray-600', bgColor: 'bg-gray-100' },
}

// Polling interval for unread count (30 seconds)
const POLL_INTERVAL = 30000

export default function NotificationBell() {
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Fetch unread count
  const fetchUnreadCount = useCallback(async () => {
    try {
      const count = await api.getUnreadNotificationCount()
      setUnreadCount(count)
    } catch (error) {
      console.error('Failed to fetch unread count:', error)
    }
  }, [])

  // Fetch notifications when dropdown opens
  const fetchNotifications = useCallback(async () => {
    setIsLoading(true)
    try {
      const response = await api.getNotifications(false, 10, 0)
      setNotifications(response.notifications)
      setUnreadCount(response.unread_count)
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Initial fetch and polling
  useEffect(() => {
    fetchUnreadCount()

    const interval = setInterval(fetchUnreadCount, POLL_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchUnreadCount])

  // Fetch notifications when dropdown opens
  useEffect(() => {
    if (isOpen) {
      fetchNotifications()
    }
  }, [isOpen, fetchNotifications])

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Mark single notification as read
  const handleMarkRead = async (notificationId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await api.markNotificationRead(notificationId)
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n))
      )
      setUnreadCount((prev) => Math.max(0, prev - 1))
    } catch (error) {
      console.error('Failed to mark notification as read:', error)
    }
  }

  // Mark all as read
  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead()
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
      setUnreadCount(0)
    } catch (error) {
      console.error('Failed to mark all as read:', error)
    }
  }

  // Handle notification click - navigate to relevant page
  const handleNotificationClick = (notification: Notification) => {
    // Mark as read first
    if (!notification.read) {
      api.markNotificationRead(notification.id).catch(console.error)
      setNotifications((prev) =>
        prev.map((n) => (n.id === notification.id ? { ...n, read: true } : n))
      )
      setUnreadCount((prev) => Math.max(0, prev - 1))
    }

    // Navigate based on notification type and data
    const { data } = notification
    if (data.shipment_id) {
      navigate(`/shipment/${data.shipment_id}`)
      setIsOpen(false)
    }
  }

  // Format relative time
  const formatRelativeTime = (dateString: string): string => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  // Get icon component for notification type
  const getNotificationIcon = (type: NotificationType) => {
    const config = NOTIFICATION_CONFIG[type] || NOTIFICATION_CONFIG.system_alert
    const IconComponent = config.icon
    return (
      <div className={`p-2 rounded-full ${config.bgColor}`}>
        <IconComponent className={`h-4 w-4 ${config.color}`} />
      </div>
    )
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-md text-gray-600 hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-1.5 py-0.5 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-500 rounded-full min-w-[18px]">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50 overflow-hidden">
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between bg-gray-50">
            <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
            <div className="flex items-center space-x-2">
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllRead}
                  className="text-xs text-primary-600 hover:text-primary-800 flex items-center"
                >
                  <CheckCheck className="h-3.5 w-3.5 mr-1" />
                  Mark all read
                </button>
              )}
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 rounded hover:bg-gray-200"
              >
                <X className="h-4 w-4 text-gray-500" />
              </button>
            </div>
          </div>

          {/* Notification List */}
          <div className="max-h-96 overflow-y-auto">
            {isLoading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto" />
                <p className="mt-2 text-sm text-gray-500">Loading notifications...</p>
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center">
                <Bell className="h-12 w-12 text-gray-300 mx-auto" />
                <p className="mt-2 text-sm text-gray-500">No notifications yet</p>
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {notifications.map((notification) => (
                  <li
                    key={notification.id}
                    onClick={() => handleNotificationClick(notification)}
                    className={`px-4 py-3 hover:bg-gray-50 cursor-pointer transition-colors ${
                      !notification.read ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      {getNotificationIcon(notification.type)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p
                            className={`text-sm font-medium ${
                              notification.read ? 'text-gray-700' : 'text-gray-900'
                            }`}
                          >
                            {notification.title}
                          </p>
                          <span className="text-xs text-gray-400 whitespace-nowrap ml-2">
                            {formatRelativeTime(notification.created_at)}
                          </span>
                        </div>
                        <p className="mt-0.5 text-sm text-gray-500 line-clamp-2">
                          {notification.message}
                        </p>
                        {typeof notification.data?.shipment_reference === 'string' && (
                          <p className="mt-1 text-xs text-gray-400">
                            Shipment: {notification.data.shipment_reference}
                          </p>
                        )}
                      </div>
                      {!notification.read && (
                        <button
                          onClick={(e) => handleMarkRead(notification.id, e)}
                          className="p-1 rounded hover:bg-gray-200 flex-shrink-0"
                          title="Mark as read"
                        >
                          <Check className="h-4 w-4 text-gray-400" />
                        </button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="px-4 py-2 border-t border-gray-200 bg-gray-50">
              <button
                onClick={() => {
                  setIsOpen(false)
                  // Could navigate to full notifications page if implemented
                }}
                className="w-full text-center text-sm text-primary-600 hover:text-primary-800"
              >
                View all notifications
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
