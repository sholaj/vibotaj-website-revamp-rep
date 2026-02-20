"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Package, CheckCircle, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { usePublicSignup } from "@/lib/api/onboarding";
import type { PublicSignupRequest } from "@/lib/api/onboarding-types";

export default function SignupCompletePage() {
  const router = useRouter();
  const signup = usePublicSignup();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Retrieve signup data from sessionStorage
    const raw = sessionStorage.getItem("tracehub_signup");
    if (!raw) {
      setError("Signup data not found. Please start the signup process again.");
      return;
    }

    try {
      const data = JSON.parse(raw) as Omit<
        PublicSignupRequest,
        "user_full_name" | "user_email"
      >;

      // In v2, the user has already registered with PropelAuth.
      // We create the organization with their info.
      // For now, use the contact email as user email (PropelAuth will provide the real one).
      const request: PublicSignupRequest = {
        ...data,
        user_full_name: "Account Owner",
        user_email: data.contact_email,
      };

      signup.mutate(request, {
        onSuccess: () => {
          sessionStorage.removeItem("tracehub_signup");
        },
        onError: (err) => {
          setError(
            err instanceof Error ? err.message : "Failed to create organization",
          );
        },
      });
    } catch {
      setError("Invalid signup data. Please start the signup process again.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="w-full max-w-md px-4">
      <div className="text-center mb-8">
        <div className="flex justify-center">
          <div className="bg-primary p-3 rounded-xl shadow-lg">
            <Package className="h-10 w-10 text-primary-foreground" />
          </div>
        </div>
        <h1 className="mt-4 text-3xl font-bold">TraceHub</h1>
      </div>

      <Card>
        <CardContent className="py-8">
          {/* Loading */}
          {signup.isPending && (
            <div className="text-center space-y-4">
              <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
              <p className="text-muted-foreground">
                Setting up your organization...
              </p>
            </div>
          )}

          {/* Success */}
          {signup.isSuccess && (
            <div className="text-center space-y-4">
              <div className="mx-auto w-16 h-16 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-xl font-semibold">
                {signup.data.organization_name} is ready!
              </h2>
              <p className="text-muted-foreground">
                {signup.data.message}
              </p>
              <Button
                className="w-full"
                onClick={() => router.push("/dashboard")}
              >
                Go to Dashboard
              </Button>
            </div>
          )}

          {/* Error */}
          {(error || signup.isError) && (
            <div className="space-y-4">
              <div className="text-center">
                <div className="mx-auto w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center mb-4">
                  <AlertCircle className="w-8 h-8 text-destructive" />
                </div>
                <h2 className="text-xl font-semibold mb-2">Setup Failed</h2>
              </div>
              <Alert variant="destructive">
                <AlertDescription>
                  {error ||
                    (signup.error instanceof Error
                      ? signup.error.message
                      : "An unexpected error occurred")}
                </AlertDescription>
              </Alert>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => router.push("/signup")}
                >
                  Try Again
                </Button>
                <Button
                  className="flex-1"
                  onClick={() => router.push("/dashboard")}
                >
                  Go to Dashboard
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
