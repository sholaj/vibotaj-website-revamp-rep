"use client";

import { PageHeader } from "@/components/domain/page-header";
import { LoadingState } from "@/components/domain/loading-state";
import { ErrorState } from "@/components/domain/error-state";
import { KpiCards } from "@/components/dashboard/kpi-cards";
import { StatusChart } from "@/components/dashboard/status-chart";
import { VolumeChart } from "@/components/dashboard/volume-chart";
import { ComplianceChart } from "@/components/dashboard/compliance-chart";
import { RecentShipments } from "@/components/dashboard/recent-shipments";
import { useDashboardStats } from "@/lib/api/shipments";

export default function DashboardPage() {
  const { data: stats, isLoading, error, refetch } = useDashboardStats();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Overview of your shipments and compliance status."
      />

      {isLoading && <LoadingState variant="cards" />}

      {error && (
        <ErrorState
          message="Failed to load dashboard data."
          onRetry={() => refetch()}
        />
      )}

      {stats && (
        <>
          <KpiCards stats={stats} />
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <StatusChart data={stats.statusBreakdown} />
            <VolumeChart data={stats.monthlyVolume} />
          </div>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <ComplianceChart data={stats.complianceTrend} />
            <RecentShipments shipments={stats.recentShipments} />
          </div>
        </>
      )}
    </div>
  );
}
