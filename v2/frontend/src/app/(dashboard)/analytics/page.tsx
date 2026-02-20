"use client";

import { useState } from "react";
import { PageHeader } from "@/components/domain/page-header";
import { LoadingState } from "@/components/domain/loading-state";
import { ErrorState } from "@/components/domain/error-state";
import { TrendsChart } from "@/components/analytics/trends-chart";
import { DocumentDistributionChart } from "@/components/analytics/document-distribution-chart";
import { CompliancePanel } from "@/components/analytics/compliance-panel";
import { TrackingStatsCard } from "@/components/analytics/tracking-stats-card";
import { AlertBanners } from "@/components/analytics/alert-banners";
import { ActivityFeed } from "@/components/analytics/activity-feed";
import {
  useAnalyticsDashboard,
  useShipmentTrends,
  useDocumentDistribution,
  useComplianceMetrics,
  useTrackingStats,
  useRecentActivity,
  type TrendGroupBy,
} from "@/lib/api/analytics";

export default function AnalyticsPage() {
  const [groupBy, setGroupBy] = useState<TrendGroupBy>("day");

  const daysMap: Record<TrendGroupBy, number> = {
    day: 30,
    week: 90,
    month: 365,
  };

  const dashboard = useAnalyticsDashboard();
  const trends = useShipmentTrends(daysMap[groupBy], groupBy);
  const distribution = useDocumentDistribution();
  const compliance = useComplianceMetrics();
  const tracking = useTrackingStats();
  const activity = useRecentActivity();

  const isLoading =
    dashboard.isLoading ||
    trends.isLoading ||
    distribution.isLoading ||
    compliance.isLoading ||
    tracking.isLoading ||
    activity.isLoading;

  const hasError =
    dashboard.error ||
    trends.error ||
    distribution.error ||
    compliance.error ||
    tracking.error ||
    activity.error;

  const refetchAll = () => {
    void dashboard.refetch();
    void trends.refetch();
    void distribution.refetch();
    void compliance.refetch();
    void tracking.refetch();
    void activity.refetch();
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Analytics"
        description="Operational insights and performance metrics."
      />

      {isLoading && <LoadingState variant="cards" />}

      {hasError && !isLoading && (
        <ErrorState
          message="Failed to load analytics data."
          onRetry={refetchAll}
        />
      )}

      {!isLoading && !hasError && (
        <>
          {dashboard.data && <AlertBanners dashboard={dashboard.data} />}

          {trends.data && (
            <TrendsChart
              data={trends.data.data}
              groupBy={groupBy}
              onGroupByChange={setGroupBy}
            />
          )}

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {distribution.data && (
              <DocumentDistributionChart data={distribution.data.data} />
            )}
            {compliance.data && (
              <CompliancePanel metrics={compliance.data} />
            )}
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {tracking.data && (
              <TrackingStatsCard stats={tracking.data} />
            )}
            <div className="lg:col-span-2">
              {activity.data && (
                <ActivityFeed activities={activity.data.activities} />
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
