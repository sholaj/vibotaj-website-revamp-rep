"use client";

import { Rocket } from "lucide-react";
import { Button } from "@/components/ui/button";

interface WelcomeStepProps {
  orgName: string;
  userName: string;
  onNext: () => void;
}

export function WelcomeStep({ orgName, userName, onNext }: WelcomeStepProps) {
  return (
    <div className="text-center space-y-6 py-8">
      <div className="mx-auto w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center">
        <Rocket className="w-10 h-10 text-primary" />
      </div>
      <div className="space-y-2">
        <h2 className="text-2xl font-bold">Welcome, {userName}!</h2>
        <p className="text-muted-foreground max-w-md mx-auto">
          Let&apos;s get <strong>{orgName}</strong> set up. This wizard will
          walk you through a few quick steps to get your team started with
          TraceHub.
        </p>
      </div>
      <div className="space-y-3">
        <p className="text-sm text-muted-foreground">
          This should take about 2 minutes.
        </p>
        <Button size="lg" onClick={onNext}>
          Let&apos;s Go
        </Button>
      </div>
    </div>
  );
}
