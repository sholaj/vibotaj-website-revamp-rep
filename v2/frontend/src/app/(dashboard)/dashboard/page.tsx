"use client";

import { useState } from "react";
import { PageHeader } from "@/components/domain/page-header";
import { LoadingState } from "@/components/domain/loading-state";
import { ErrorState } from "@/components/domain/error-state";
import { KpiCards } from "@/components/dashboard/kpi-cards";
import { StatusChart } from "@/components/dashboard/status-chart";
import { VolumeChart } from "@/components/dashboard/volume-chart";
import { ComplianceChart } from "@/components/dashboard/compliance-chart";
import { RecentShipments } from "@/components/dashboard/recent-shipments";
import { TrialBanner } from "@/components/dashboard/trial-banner";
import { OnboardingWizard } from "@/components/onboarding/onboarding-wizard";
import { useDashboardStats } from "@/lib/api/shipments";
import { useOnboardingState } from "@/lib/api/onboarding";
import { useCurrentOrg } from "@/lib/auth/org-context";

export default function DashboardPage() {
  const { data: stats, isLoading, error, refetch } = useDashboardStats();
  const { orgId } = useCurrentOrg();
  const { data: onboardingState } = useOnboardingState(orgId);
  const [wizardDismissed, setWizardDismissed] = useState(false);

  // Show onboarding wizard if org is in pending_setup
  const showWizard =
    !wizardDismissed &&
    onboardingState?.status === "pending_setup";

  // Show trial banner if org has a paid plan with trial
  const showTrialBanner =
    onboardingState?.plan?.trial_ends_at &&
    onboardingState?.plan?.tier !== "free" &&
    onboardingState?.status === "active";

  if (showWizard && onboardingState && orgId) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Welcome to TraceHub"
          description="Complete setup to start tracking your shipments."
        />
        <OnboardingWizard
          orgId={orgId}
          orgName="Your Organization"
          userName="there"
          completedSteps={onboardingState.onboarding.completed_steps}
          onComplete={() => setWizardDismissed(true)}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Overview of your shipments and compliance status."
      />

      {showTrialBanner && onboardingState?.plan?.trial_ends_at && (
        <TrialBanner
          trialEndsAt={onboardingState.plan.trial_ends_at}
          planTier={onboardingState.plan.tier}
        />
      )}

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
