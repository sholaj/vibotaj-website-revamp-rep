/**
 * TypeScript types for the onboarding API.
 * PRD-024: Self-Service Onboarding Flow
 */

export type PlanTier = "free" | "starter" | "professional" | "enterprise";

export type OnboardingStep =
  | "profile"
  | "organization"
  | "invite_team"
  | "tour";

export type OrgType = "vibotaj" | "buyer" | "supplier" | "logistics_agent";

export type OrgStatus = "active" | "suspended" | "pending_setup";

export interface PlanInfo {
  tier: PlanTier;
  selected_at: string | null;
  trial_ends_at: string | null;
}

export interface OnboardingState {
  completed_steps: OnboardingStep[];
  completed_at: string | null;
  skipped_at: string | null;
}

export interface PublicSignupRequest {
  org_name: string;
  org_slug: string;
  org_type: OrgType;
  contact_email: string;
  contact_phone?: string;
  plan_tier: PlanTier;
  user_full_name: string;
  user_email: string;
}

export interface PublicSignupResponse {
  organization_id: string;
  organization_name: string;
  organization_slug: string;
  status: OrgStatus;
  plan: PlanInfo;
  message: string;
}

export interface OnboardingStateResponse {
  organization_id: string;
  status: OrgStatus;
  plan: PlanInfo;
  onboarding: OnboardingState;
  all_steps_completed: boolean;
}

export interface OnboardingCompleteResponse {
  organization_id: string;
  status: OrgStatus;
  message: string;
}

export interface SlugCheckResponse {
  slug: string;
  available: boolean;
  suggestion: string | null;
}

export interface PlanCard {
  tier: PlanTier;
  name: string;
  description: string;
  price: string;
  period: string;
  features: string[];
  highlighted: boolean;
}

export const PLAN_CARDS: PlanCard[] = [
  {
    tier: "free",
    name: "Free",
    description: "For small teams getting started",
    price: "$0",
    period: "forever",
    features: [
      "Up to 5 shipments/month",
      "Basic document management",
      "1 team member",
      "Email support",
    ],
    highlighted: false,
  },
  {
    tier: "starter",
    name: "Starter",
    description: "For growing businesses",
    price: "$49",
    period: "/month",
    features: [
      "Up to 50 shipments/month",
      "Full document management",
      "5 team members",
      "Compliance monitoring",
      "Priority support",
    ],
    highlighted: false,
  },
  {
    tier: "professional",
    name: "Professional",
    description: "For established operations",
    price: "$149",
    period: "/month",
    features: [
      "Unlimited shipments",
      "Advanced compliance",
      "25 team members",
      "API access",
      "Custom integrations",
      "Dedicated support",
    ],
    highlighted: true,
  },
  {
    tier: "enterprise",
    name: "Enterprise",
    description: "For large organizations",
    price: "Custom",
    period: "",
    features: [
      "Everything in Professional",
      "Unlimited team members",
      "SSO/SAML",
      "Custom SLAs",
      "On-premise option",
      "Account manager",
    ],
    highlighted: false,
  },
];
