"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  PublicSignupRequest,
  PublicSignupResponse,
  OnboardingStateResponse,
  OnboardingStep,
  OnboardingCompleteResponse,
  SlugCheckResponse,
} from "./onboarding-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function authHeaders(orgId: string): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-Organization-Id": orgId,
  };
}

// --- Fetch functions ---

async function checkSlug(slug: string): Promise<SlugCheckResponse> {
  const res = await fetch(`${API_BASE}/api/public/check-slug/${slug}`);
  if (!res.ok) throw new Error(`Failed to check slug: ${res.status}`);
  return res.json() as Promise<SlugCheckResponse>;
}

async function publicSignup(
  request: PublicSignupRequest,
): Promise<PublicSignupResponse> {
  const res = await fetch(`${API_BASE}/api/public/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail?.message || `Signup failed: ${res.status}`);
  }
  return res.json() as Promise<PublicSignupResponse>;
}

async function fetchOnboardingState(
  orgId: string,
): Promise<OnboardingStateResponse> {
  const res = await fetch(
    `${API_BASE}/api/organizations/${orgId}/onboarding`,
    { headers: authHeaders(orgId) },
  );
  if (!res.ok) throw new Error(`Failed to fetch onboarding: ${res.status}`);
  return res.json() as Promise<OnboardingStateResponse>;
}

async function updateOnboardingStep(
  orgId: string,
  step: OnboardingStep,
): Promise<OnboardingStateResponse> {
  const res = await fetch(
    `${API_BASE}/api/organizations/${orgId}/onboarding`,
    {
      method: "PATCH",
      headers: authHeaders(orgId),
      body: JSON.stringify({ step }),
    },
  );
  if (!res.ok)
    throw new Error(`Failed to update onboarding: ${res.status}`);
  return res.json() as Promise<OnboardingStateResponse>;
}

async function completeOnboarding(
  orgId: string,
  skip: boolean = false,
): Promise<OnboardingCompleteResponse> {
  const res = await fetch(
    `${API_BASE}/api/organizations/${orgId}/onboarding/complete`,
    {
      method: "POST",
      headers: authHeaders(orgId),
      body: JSON.stringify({ skip }),
    },
  );
  if (!res.ok)
    throw new Error(`Failed to complete onboarding: ${res.status}`);
  return res.json() as Promise<OnboardingCompleteResponse>;
}

// --- React Query hooks ---

export function useCheckSlug(slug: string) {
  return useQuery({
    queryKey: ["check-slug", slug],
    queryFn: () => checkSlug(slug),
    enabled: slug.length >= 2,
    staleTime: 10_000,
  });
}

export function usePublicSignup() {
  return useMutation({
    mutationFn: publicSignup,
  });
}

export function useOnboardingState(orgId: string | null) {
  return useQuery({
    queryKey: ["onboarding", orgId],
    queryFn: () => fetchOnboardingState(orgId!),
    enabled: !!orgId,
    staleTime: 30_000,
  });
}

export function useUpdateOnboardingStep(orgId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (step: OnboardingStep) =>
      updateOnboardingStep(orgId, step),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["onboarding", orgId],
      });
    },
  });
}

export function useCompleteOnboarding(orgId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (skip: boolean) => completeOnboarding(orgId, skip),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["onboarding", orgId],
      });
      void queryClient.invalidateQueries({
        queryKey: ["organization"],
      });
    },
  });
}
