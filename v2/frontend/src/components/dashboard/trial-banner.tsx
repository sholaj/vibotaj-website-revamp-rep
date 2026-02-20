"use client";

import { Clock, ArrowRight } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

interface TrialBannerProps {
  trialEndsAt: string;
  planTier: string;
}

export function TrialBanner({ trialEndsAt, planTier }: TrialBannerProps) {
  const endDate = new Date(trialEndsAt);
  const now = new Date();
  const diffMs = endDate.getTime() - now.getTime();
  const daysLeft = Math.max(0, Math.ceil(diffMs / (1000 * 60 * 60 * 24)));

  if (daysLeft <= 0) {
    return (
      <Alert variant="destructive">
        <Clock className="h-4 w-4" />
        <AlertTitle>Trial Expired</AlertTitle>
        <AlertDescription className="flex items-center justify-between">
          <span>
            Your {planTier} trial has expired. Upgrade to continue using
            premium features.
          </span>
          <Button size="sm" variant="outline" className="ml-4 shrink-0">
            Upgrade Now
            <ArrowRight className="w-3 h-3 ml-1" />
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  const isUrgent = daysLeft <= 3;

  return (
    <Alert variant={isUrgent ? "destructive" : "default"}>
      <Clock className="h-4 w-4" />
      <AlertTitle>
        {daysLeft} day{daysLeft !== 1 ? "s" : ""} left in your{" "}
        {planTier} trial
      </AlertTitle>
      <AlertDescription className="flex items-center justify-between">
        <span>
          Your trial ends on {endDate.toLocaleDateString()}. Upgrade to
          keep all features.
        </span>
        <Button size="sm" variant="outline" className="ml-4 shrink-0">
          Upgrade
          <ArrowRight className="w-3 h-3 ml-1" />
        </Button>
      </AlertDescription>
    </Alert>
  );
}
