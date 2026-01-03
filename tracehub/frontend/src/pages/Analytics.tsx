/**
 * Analytics Dashboard Page
 *
 * Displays comprehensive analytics including:
 * - Key metric cards (shipments, documents, compliance)
 * - Shipment trends over time (line chart)
 * - Document status distribution (pie/bar chart)
 * - Recent activity feed
 */

import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  BarChart3,
  TrendingUp,
  Package,
  FileText,
  Shield,
  Activity,
  Clock,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  AlertCircle,
  ArrowRight,
} from 'lucide-react'
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { format, parseISO } from 'date-fns'
import api, { ApiClientError, NetworkError } from '../api/client'
import type {
  DashboardStats,
  ShipmentTrendsResponse,
  DocumentDistributionResponse,
  RecentActivityResponse,
  ActivityItem,
} from '../types'

// Status colors for charts
const STATUS_COLORS: Record<string, string> = {
  draft: '#9CA3AF',
  uploaded: '#3B82F6',
  validated: '#10B981',
  compliance_ok: '#059669',
  compliance_failed: '#EF4444',
  linked: '#8B5CF6',
  archived: '#6B7280',
}

// Document status labels
const STATUS_LABELS: Record<string, string> = {
  draft: 'Draft',
  uploaded: 'Uploaded',
  validated: 'Validated',
  compliance_ok: 'Compliant',
  compliance_failed: 'Failed',
  linked: 'Linked',
  archived: 'Archived',
}

// Action labels for activity feed
const ACTION_LABELS: Record<string, string> = {
  'auth.login.success': 'Logged in',
  'shipment.view': 'Viewed shipment',
  'document.upload': 'Uploaded document',
  'document.download': 'Downloaded document',
  'document.validate': 'Validated document',
  'document.transition': 'Updated document status',
  'tracking.refresh': 'Refreshed tracking',
  'auditpack.download': 'Downloaded audit pack',
}

// Metric Card Component
function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  color = 'primary',
  link,
}: {
  title: string
  value: number | string
  subtitle?: string
  icon: React.ElementType
  trend?: { value: number; label: string }
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  link?: string
}) {
  const colorClasses = {
    primary: 'bg-primary-50 text-primary-600',
    success: 'bg-green-50 text-green-600',
    warning: 'bg-yellow-50 text-yellow-600',
    danger: 'bg-red-50 text-red-600',
    info: 'bg-blue-50 text-blue-600',
  }

  const content = (
    <div className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="h-6 w-6" />
        </div>
        {trend && (
          <div
            className={`flex items-center text-sm ${
              trend.value >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            <TrendingUp className={`h-4 w-4 mr-1 ${trend.value < 0 ? 'rotate-180' : ''}`} />
            {Math.abs(trend.value)}%
          </div>
        )}
      </div>
      <div className="mt-4">
        <h3 className="text-2xl font-bold text-gray-900">{value}</h3>
        <p className="text-sm text-gray-600 mt-1">{title}</p>
        {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
      </div>
      {link && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <span className="text-sm text-primary-600 flex items-center hover:text-primary-700">
            View details <ArrowRight className="h-4 w-4 ml-1" />
          </span>
        </div>
      )}
    </div>
  )

  if (link) {
    return <Link to={link}>{content}</Link>
  }

  return content
}

// Progress Circle Component
function ProgressCircle({
  value,
  max = 100,
  label,
  color = '#3B82F6',
}: {
  value: number
  max?: number
  label: string
  color?: string
}) {
  const percentage = (value / max) * 100
  const circumference = 2 * Math.PI * 40 // radius = 40
  const strokeDashoffset = circumference - (percentage / 100) * circumference

  return (
    <div className="flex flex-col items-center">
      <div className="relative">
        <svg className="w-24 h-24 transform -rotate-90">
          <circle
            cx="48"
            cy="48"
            r="40"
            fill="none"
            stroke="#E5E7EB"
            strokeWidth="8"
          />
          <circle
            cx="48"
            cy="48"
            r="40"
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl font-bold text-gray-900">{Math.round(percentage)}%</span>
        </div>
      </div>
      <span className="mt-2 text-sm text-gray-600">{label}</span>
    </div>
  )
}

// Activity Item Component
function ActivityItemRow({ activity }: { activity: ActivityItem }) {
  const actionLabel = ACTION_LABELS[activity.action] || activity.action.split('.').pop()

  return (
    <div className="flex items-start py-3 border-b border-gray-100 last:border-0">
      <div className="flex-shrink-0">
        <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
          <Activity className="h-4 w-4 text-gray-600" />
        </div>
      </div>
      <div className="ml-3 flex-1 min-w-0">
        <p className="text-sm text-gray-900">
          <span className="font-medium">{activity.username}</span>{' '}
          {actionLabel}
          {activity.resource_id && (
            <span className="text-gray-500"> ({activity.resource_type})</span>
          )}
        </p>
        <p className="text-xs text-gray-500 mt-0.5">
          {format(parseISO(activity.timestamp), 'MMM d, h:mm a')}
        </p>
      </div>
    </div>
  )
}

// Loading Skeleton
function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-lg shadow-sm p-6">
            <div className="h-12 w-12 bg-gray-200 rounded-lg"></div>
            <div className="h-8 w-20 bg-gray-200 rounded mt-4"></div>
            <div className="h-4 w-32 bg-gray-200 rounded mt-2"></div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="h-6 w-40 bg-gray-200 rounded"></div>
          <div className="h-64 bg-gray-200 rounded mt-4"></div>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="h-6 w-40 bg-gray-200 rounded"></div>
          <div className="h-64 bg-gray-200 rounded mt-4"></div>
        </div>
      </div>
    </div>
  )
}

// Error Display
function ErrorDisplay({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
      <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-red-800 mb-2">Failed to Load Analytics</h3>
      <p className="text-red-600 mb-4">{message}</p>
      <button onClick={onRetry} className="btn-primary">
        <RefreshCw className="h-4 w-4 mr-2" />
        Try Again
      </button>
    </div>
  )
}

export default function Analytics() {
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null)
  const [trends, setTrends] = useState<ShipmentTrendsResponse | null>(null)
  const [docDistribution, setDocDistribution] = useState<DocumentDistributionResponse | null>(null)
  const [recentActivity, setRecentActivity] = useState<RecentActivityResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAnalytics = useCallback(async (showLoading = true) => {
    if (showLoading) {
      setIsLoading(true)
    } else {
      setIsRefreshing(true)
    }
    setError(null)

    try {
      // Fetch all analytics data in parallel
      const [statsData, trendsData, docDistData, activityData] = await Promise.all([
        api.getDashboardStats(),
        api.getShipmentTrends(30, 'day'),
        api.getDocumentDistribution(),
        api.getRecentActivity(10),
      ])

      setDashboardStats(statsData)
      setTrends(trendsData)
      setDocDistribution(docDistData)
      setRecentActivity(activityData)
    } catch (err) {
      console.error('Failed to fetch analytics:', err)
      if (err instanceof NetworkError) {
        setError('Unable to connect to the server. Please check your connection.')
      } else if (err instanceof ApiClientError) {
        setError(err.message || 'Failed to load analytics data')
      } else {
        setError('An unexpected error occurred')
      }
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }, [])

  useEffect(() => {
    fetchAnalytics()
  }, [fetchAnalytics])

  const handleRefresh = useCallback(() => {
    api.invalidateCache('/analytics')
    api.invalidateCache('/audit-log')
    fetchAnalytics(false)
  }, [fetchAnalytics])

  // Prepare chart data
  const trendChartData = trends?.data.map((item) => ({
    date: format(parseISO(item.date), 'MMM d'),
    count: item.count,
  })) || []

  const pieChartData = docDistribution?.data
    .filter((item) => item.count > 0)
    .map((item) => ({
      name: STATUS_LABELS[item.status] || item.status,
      value: item.count,
      color: STATUS_COLORS[item.status] || '#6B7280',
    })) || []

  if (isLoading) {
    return (
      <div>
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">Loading operational insights...</p>
        </div>
        <LoadingSkeleton />
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
        </div>
        <ErrorDisplay message={error} onRetry={() => fetchAnalytics()} />
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Operational insights and performance metrics
            {dashboardStats && (
              <span className="text-sm text-gray-500 ml-2">
                Last updated: {format(parseISO(dashboardStats.generated_at), 'h:mm a')}
              </span>
            )}
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="btn-secondary"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
          {isRefreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Key Metrics Grid */}
      {dashboardStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <MetricCard
            title="Total Shipments"
            value={dashboardStats.shipments.total}
            subtitle={`${dashboardStats.shipments.in_transit} in transit`}
            icon={Package}
            color="primary"
            link="/dashboard"
          />
          <MetricCard
            title="Document Completion"
            value={`${dashboardStats.documents.completion_rate}%`}
            subtitle={`${dashboardStats.documents.pending_validation} pending validation`}
            icon={FileText}
            color="info"
          />
          <MetricCard
            title="Compliance Rate"
            value={`${dashboardStats.compliance.rate}%`}
            subtitle={`${dashboardStats.compliance.needing_attention} need attention`}
            icon={Shield}
            color={dashboardStats.compliance.rate >= 80 ? 'success' : 'warning'}
          />
          <MetricCard
            title="Tracking Events Today"
            value={dashboardStats.tracking.events_today}
            subtitle={`${dashboardStats.tracking.containers_tracked} containers tracked`}
            icon={Activity}
            color="success"
          />
        </div>
      )}

      {/* Alert Cards */}
      {dashboardStats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {dashboardStats.documents.expiring_soon > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-center">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mr-3 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-yellow-800">
                  {dashboardStats.documents.expiring_soon} document(s) expiring soon
                </p>
                <p className="text-xs text-yellow-600">Within the next 30 days</p>
              </div>
            </div>
          )}
          {dashboardStats.shipments.with_delays > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
              <Clock className="h-5 w-5 text-red-600 mr-3 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-red-800">
                  {dashboardStats.shipments.with_delays} shipment(s) delayed
                </p>
                <p className="text-xs text-red-600">May require attention</p>
              </div>
            </div>
          )}
          {dashboardStats.compliance.needing_attention === 0 && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center">
              <CheckCircle2 className="h-5 w-5 text-green-600 mr-3 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-green-800">
                  All shipments compliant
                </p>
                <p className="text-xs text-green-600">No compliance issues detected</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Shipments Over Time */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <TrendingUp className="h-5 w-5 mr-2 text-primary-600" />
            Shipments Over Time
          </h3>
          {trendChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12, fill: '#6B7280' }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: '#6B7280' }}
                  tickLine={false}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  dot={{ fill: '#3B82F6', strokeWidth: 2 }}
                  activeDot={{ r: 6 }}
                  name="Shipments"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No shipment data available for the selected period
            </div>
          )}
        </div>

        {/* Document Status Distribution */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <BarChart3 className="h-5 w-5 mr-2 text-primary-600" />
            Document Status Distribution
          </h3>
          {pieChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  nameKey="name"
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                  labelLine={false}
                >
                  {pieChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No document data available
            </div>
          )}
        </div>
      </div>

      {/* Bottom Row: Compliance Progress + Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Compliance Overview */}
        {dashboardStats && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Shield className="h-5 w-5 mr-2 text-primary-600" />
              Compliance Overview
            </h3>
            <div className="flex justify-around items-center py-4">
              <ProgressCircle
                value={dashboardStats.compliance.rate}
                label="Overall Compliance"
                color={dashboardStats.compliance.rate >= 80 ? '#10B981' : '#F59E0B'}
              />
              <ProgressCircle
                value={dashboardStats.compliance.eudr_coverage}
                label="EUDR Coverage"
                color="#3B82F6"
              />
            </div>
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Shipments needing attention</span>
                <span className="font-medium text-gray-900">
                  {dashboardStats.compliance.needing_attention}
                </span>
              </div>
              <div className="flex justify-between text-sm mt-2">
                <span className="text-gray-600">Documents expiring soon</span>
                <span className="font-medium text-gray-900">
                  {dashboardStats.documents.expiring_soon}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Recent Activity */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Activity className="h-5 w-5 mr-2 text-primary-600" />
            Recent Activity
          </h3>
          {recentActivity && recentActivity.activities.length > 0 ? (
            <div className="space-y-1">
              {recentActivity.activities.map((activity) => (
                <ActivityItemRow key={activity.id} activity={activity} />
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No recent activity to display
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
