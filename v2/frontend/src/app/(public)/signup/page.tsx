"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Package, Building2, ArrowRight, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { PlanSelector } from "@/components/onboarding/plan-selector";
import { useCheckSlug } from "@/lib/api/onboarding";
import type { PlanTier, OrgType } from "@/lib/api/onboarding-types";

type Step = "plan" | "details";

const ORG_TYPE_OPTIONS: { value: OrgType; label: string }[] = [
  { value: "buyer", label: "Buyer / Importer" },
  { value: "supplier", label: "Supplier / Exporter" },
  { value: "logistics_agent", label: "Logistics / Freight Agent" },
];

export default function SignupPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("plan");
  const [formError, setFormError] = useState("");

  // Plan selection
  const [planTier, setPlanTier] = useState<PlanTier>("professional");

  // Org details
  const [orgName, setOrgName] = useState("");
  const [orgSlug, setOrgSlug] = useState("");
  const [orgType, setOrgType] = useState<OrgType | "">("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");

  // Slug check
  const slugToCheck = orgSlug.length >= 2 ? orgSlug : "";
  const { data: slugCheck } = useCheckSlug(slugToCheck);

  // Auto-generate slug from org name
  const handleOrgNameChange = (name: string) => {
    setOrgName(name);
    // Only auto-generate if user hasn't manually edited the slug
    if (!orgSlug || orgSlug === generateSlug(orgName)) {
      setOrgSlug(generateSlug(name));
    }
  };

  const handleContinueToDetails = () => {
    setStep("details");
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");

    if (!orgName.trim() || orgName.trim().length < 2) {
      setFormError("Organization name must be at least 2 characters");
      return;
    }
    if (!orgSlug || orgSlug.length < 2) {
      setFormError("Organization slug is required");
      return;
    }
    if (slugCheck && !slugCheck.available) {
      setFormError(
        `Slug "${orgSlug}" is already taken. Try "${slugCheck.suggestion}"`,
      );
      return;
    }
    if (!orgType) {
      setFormError("Please select your organization type");
      return;
    }
    if (!contactEmail) {
      setFormError("Contact email is required");
      return;
    }

    // Store signup data in sessionStorage and redirect to PropelAuth signup
    const signupData = {
      org_name: orgName.trim(),
      org_slug: orgSlug,
      org_type: orgType,
      contact_email: contactEmail,
      contact_phone: contactPhone || undefined,
      plan_tier: planTier,
    };
    sessionStorage.setItem("tracehub_signup", JSON.stringify(signupData));
    router.push("/signup/complete");
  };

  return (
    <div className="w-full max-w-5xl px-4 py-8">
      {/* Logo and Title */}
      <div className="text-center mb-8">
        <div className="flex justify-center">
          <div className="bg-primary p-3 rounded-xl shadow-lg">
            <Package className="h-10 w-10 text-primary-foreground" />
          </div>
        </div>
        <h1 className="mt-4 text-3xl font-bold">Get started with TraceHub</h1>
        <p className="mt-2 text-muted-foreground">
          Set up your organization in minutes
        </p>
      </div>

      {/* Step 1: Plan Selection */}
      {step === "plan" && (
        <div className="space-y-6">
          <div className="text-center">
            <h2 className="text-xl font-semibold">Choose your plan</h2>
            <p className="text-sm text-muted-foreground mt-1">
              All paid plans include a 14-day free trial. No credit card
              required.
            </p>
          </div>

          <PlanSelector selectedPlan={planTier} onSelect={setPlanTier} />

          <div className="flex justify-center">
            <Button size="lg" onClick={handleContinueToDetails}>
              Continue
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      )}

      {/* Step 2: Organization Details */}
      {step === "details" && (
        <div className="flex justify-center">
          <Card className="w-full max-w-lg">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-primary" />
                <CardTitle>Organization Details</CardTitle>
              </div>
              <CardDescription>
                Tell us about your organization
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {formError && (
                  <Alert variant="destructive">
                    <AlertDescription>{formError}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="orgName">Organization Name</Label>
                  <Input
                    id="orgName"
                    value={orgName}
                    onChange={(e) => handleOrgNameChange(e.target.value)}
                    placeholder="Acme Trading Co."
                    required
                    autoFocus
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="orgSlug">URL Slug</Label>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground whitespace-nowrap">
                      tracehub.vibotaj.com/
                    </span>
                    <Input
                      id="orgSlug"
                      value={orgSlug}
                      onChange={(e) =>
                        setOrgSlug(
                          e.target.value
                            .toLowerCase()
                            .replace(/[^a-z0-9-]/g, ""),
                        )
                      }
                      placeholder="acme-trading"
                      required
                    />
                  </div>
                  {slugCheck && !slugCheck.available && (
                    <p className="text-sm text-destructive">
                      This slug is taken.{" "}
                      {slugCheck.suggestion && (
                        <button
                          type="button"
                          className="underline"
                          onClick={() => setOrgSlug(slugCheck.suggestion!)}
                        >
                          Use &quot;{slugCheck.suggestion}&quot;
                        </button>
                      )}
                    </p>
                  )}
                  {slugCheck && slugCheck.available && orgSlug.length >= 2 && (
                    <p className="text-sm text-green-600">
                      Slug is available
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="orgType">Organization Type</Label>
                  <Select
                    value={orgType}
                    onValueChange={(v) => setOrgType(v as OrgType)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select type..." />
                    </SelectTrigger>
                    <SelectContent>
                      {ORG_TYPE_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="contactEmail">Contact Email</Label>
                  <Input
                    id="contactEmail"
                    type="email"
                    value={contactEmail}
                    onChange={(e) => setContactEmail(e.target.value)}
                    placeholder="contact@acme.com"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="contactPhone">
                    Phone{" "}
                    <span className="text-muted-foreground">(optional)</span>
                  </Label>
                  <Input
                    id="contactPhone"
                    type="tel"
                    value={contactPhone}
                    onChange={(e) => setContactPhone(e.target.value)}
                    placeholder="+234 xxx xxx xxxx"
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setStep("plan")}
                  >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back
                  </Button>
                  <Button type="submit" className="flex-1">
                    Create Organization
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

function generateSlug(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}
