"use client";

import { Check } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { PlanTier } from "@/lib/api/onboarding-types";
import { PLAN_CARDS } from "@/lib/api/onboarding-types";

interface PlanSelectorProps {
  selectedPlan: PlanTier;
  onSelect: (tier: PlanTier) => void;
}

export function PlanSelector({ selectedPlan, onSelect }: PlanSelectorProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {PLAN_CARDS.map((plan) => {
        const isSelected = selectedPlan === plan.tier;

        return (
          <Card
            key={plan.tier}
            className={cn(
              "relative cursor-pointer transition-all hover:shadow-md",
              isSelected && "ring-2 ring-primary",
              plan.highlighted &&
                !isSelected &&
                "border-primary/50 shadow-sm",
            )}
            onClick={() => onSelect(plan.tier)}
          >
            {plan.highlighted && (
              <Badge className="absolute -top-2.5 left-1/2 -translate-x-1/2">
                Most Popular
              </Badge>
            )}
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">{plan.name}</CardTitle>
              <p className="text-sm text-muted-foreground">
                {plan.description}
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-bold">{plan.price}</span>
                {plan.period && (
                  <span className="text-sm text-muted-foreground">
                    {plan.period}
                  </span>
                )}
              </div>

              {plan.tier !== "free" && (
                <p className="text-xs text-muted-foreground">
                  14-day free trial
                </p>
              )}

              <ul className="space-y-2">
                {plan.features.map((feature) => (
                  <li
                    key={feature}
                    className="flex items-start text-sm"
                  >
                    <Check className="mr-2 h-4 w-4 shrink-0 text-green-600 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <Button
                variant={isSelected ? "default" : "outline"}
                className="w-full"
                onClick={(e) => {
                  e.stopPropagation();
                  onSelect(plan.tier);
                }}
              >
                {isSelected ? "Selected" : "Select"}
              </Button>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
