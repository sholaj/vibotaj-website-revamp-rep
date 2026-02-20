"use client";

import { useState } from "react";
import { Building2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface OrgSetupStepProps {
  orgName: string;
  onNext: () => void;
  onBack: () => void;
}

export function OrgSetupStep({ orgName, onNext, onBack }: OrgSetupStepProps) {
  const [taxId, setTaxId] = useState("");
  const [regNumber, setRegNumber] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // These details are optional — user can fill them in later from settings
    onNext();
  };

  return (
    <div className="space-y-6 py-4">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 bg-primary/10 rounded-full flex items-center justify-center">
          <Building2 className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-xl font-semibold">Organization Details</h2>
          <p className="text-sm text-muted-foreground">
            Add optional business details for {orgName}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="taxId">
            Tax ID{" "}
            <span className="text-muted-foreground">(optional)</span>
          </Label>
          <Input
            id="taxId"
            value={taxId}
            onChange={(e) => setTaxId(e.target.value)}
            placeholder="e.g., DE123456789"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="regNumber">
            Registration Number{" "}
            <span className="text-muted-foreground">(optional)</span>
          </Label>
          <Input
            id="regNumber"
            value={regNumber}
            onChange={(e) => setRegNumber(e.target.value)}
            placeholder="e.g., RC1479592"
          />
        </div>

        <p className="text-xs text-muted-foreground">
          You can always update these details later in Settings.
        </p>

        <div className="flex gap-3 pt-2">
          <Button type="button" variant="outline" onClick={onBack}>
            Back
          </Button>
          <Button type="submit" className="flex-1">
            Continue
          </Button>
          <Button type="button" variant="ghost" onClick={onNext}>
            Skip
          </Button>
        </div>
      </form>
    </div>
  );
}
