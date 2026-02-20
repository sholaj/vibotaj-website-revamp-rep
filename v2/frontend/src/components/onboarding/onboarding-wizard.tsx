"use client";

import { useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StepIndicator } from "./step-indicator";
import { WelcomeStep } from "./welcome-step";
import { OrgSetupStep } from "./org-setup-step";
import { InviteTeamStep } from "./invite-team-step";
import { TourStep } from "./tour-step";
import {
  useUpdateOnboardingStep,
  useCompleteOnboarding,
} from "@/lib/api/onboarding";
import type { OnboardingStep } from "@/lib/api/onboarding-types";

const STEPS: { id: OnboardingStep; label: string }[] = [
  { id: "profile", label: "Welcome" },
  { id: "organization", label: "Organization" },
  { id: "invite_team", label: "Team" },
  { id: "tour", label: "Tour" },
];

interface OnboardingWizardProps {
  orgId: string;
  orgName: string;
  userName: string;
  completedSteps: OnboardingStep[];
  onComplete: () => void;
}

export function OnboardingWizard({
  orgId,
  orgName,
  userName,
  completedSteps,
  onComplete,
}: OnboardingWizardProps) {
  // Start at the first incomplete step
  const firstIncomplete = STEPS.findIndex(
    (s) => !completedSteps.includes(s.id),
  );
  const [currentStep, setCurrentStep] = useState(
    firstIncomplete >= 0 ? firstIncomplete : 0,
  );

  const updateStep = useUpdateOnboardingStep(orgId);
  const completeOnboarding = useCompleteOnboarding(orgId);

  const markStepAndAdvance = useCallback(
    (stepId: OnboardingStep) => {
      updateStep.mutate(stepId);
      if (currentStep < STEPS.length - 1) {
        setCurrentStep(currentStep + 1);
      }
    },
    [currentStep, updateStep],
  );

  const handleComplete = useCallback(() => {
    // Mark last step and complete onboarding
    updateStep.mutate("tour");
    completeOnboarding.mutate(false, {
      onSuccess: () => onComplete(),
    });
  }, [updateStep, completeOnboarding, onComplete]);

  const handleSkip = () => {
    completeOnboarding.mutate(true, {
      onSuccess: () => onComplete(),
    });
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <StepIndicator
          steps={STEPS}
          currentStep={currentStep}
          completedSteps={completedSteps}
        />
        <Button variant="ghost" size="sm" onClick={handleSkip}>
          Skip Setup
        </Button>
      </div>

      <Card>
        <CardContent className="p-6">
          {currentStep === 0 && (
            <WelcomeStep
              orgName={orgName}
              userName={userName}
              onNext={() => markStepAndAdvance("profile")}
            />
          )}
          {currentStep === 1 && (
            <OrgSetupStep
              orgName={orgName}
              onNext={() => markStepAndAdvance("organization")}
              onBack={() => setCurrentStep(0)}
            />
          )}
          {currentStep === 2 && (
            <InviteTeamStep
              orgId={orgId}
              onNext={() => markStepAndAdvance("invite_team")}
              onBack={() => setCurrentStep(1)}
            />
          )}
          {currentStep === 3 && (
            <TourStep
              onComplete={handleComplete}
              onBack={() => setCurrentStep(2)}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
