"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Package,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle,
  XCircle,
  Building2,
  Mail,
  Shield,
  LogIn,
  LogOut,
  User,
  Loader2,
} from "lucide-react";
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
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useUser, useLogoutFunction } from "@propelauth/nextjs/client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type OrgRole = "admin" | "manager" | "member" | "viewer";

interface InvitationInfo {
  invitation_id: string;
  organization_name: string;
  organization_type: string;
  email: string;
  org_role: OrgRole;
  requires_registration: boolean;
  custom_message: string | null;
  invited_by_name: string | null;
  expires_at: string;
}

interface AcceptResponse {
  success: boolean;
  message: string;
  user_id: string;
  organization_id: string;
  organization_name: string;
  org_role: OrgRole;
  is_new_user: boolean;
}

const ROLE_LABELS: Record<OrgRole, string> = {
  admin: "Administrator",
  manager: "Manager",
  member: "Member",
  viewer: "Viewer",
};

const ROLE_DESCRIPTIONS: Record<OrgRole, string> = {
  admin:
    "Full access to manage organization settings, members, and all data",
  manager: "Can manage shipments, documents, and invite members",
  member: "Can view and manage shipments and documents",
  viewer: "Read-only access to shipments and documents",
};

function PasswordStrength({ password }: { password: string }) {
  const checks = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /\d/.test(password),
  };

  const passedCount = Object.values(checks).filter(Boolean).length;
  const strengthColors = [
    "bg-red-500",
    "bg-yellow-500",
    "bg-yellow-400",
    "bg-green-500",
  ];
  const strengthLabels = ["Weak", "Fair", "Good", "Strong"];

  if (password.length === 0) return null;

  return (
    <div className="mt-2 space-y-1">
      <div className="flex gap-1">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded ${
              i < passedCount ? strengthColors[passedCount - 1] : "bg-muted"
            }`}
          />
        ))}
      </div>
      <p className="text-xs text-muted-foreground">
        Password strength: {strengthLabels[passedCount - 1] || "Very weak"}
      </p>
      <ul className="text-xs text-muted-foreground space-y-0.5">
        <li className={checks.length ? "text-green-600" : ""}>
          {checks.length ? "\u2713" : "\u25CB"} At least 8 characters
        </li>
        <li className={checks.uppercase ? "text-green-600" : ""}>
          {checks.uppercase ? "\u2713" : "\u25CB"} One uppercase letter
        </li>
        <li className={checks.lowercase ? "text-green-600" : ""}>
          {checks.lowercase ? "\u2713" : "\u25CB"} One lowercase letter
        </li>
        <li className={checks.number ? "text-green-600" : ""}>
          {checks.number ? "\u2713" : "\u25CB"} One number
        </li>
      </ul>
    </div>
  );
}

export default function AcceptInvitationPage() {
  const params = useParams<{ token: string }>();
  const token = params.token;
  const router = useRouter();
  const { loading: authLoading, isLoggedIn, user } = useUser();
  const logout = useLogoutFunction();

  // State
  const [invitation, setInvitation] = useState<InvitationInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [acceptSuccess, setAcceptSuccess] = useState<AcceptResponse | null>(
    null,
  );

  // Form state for new users
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState("");

  // Fetch invitation details
  const fetchInvitation = useCallback(async () => {
    if (!token) {
      setError("Invalid invitation link");
      setIsLoading(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/invitations/accept/${token}`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(
          data.detail || "This invitation is invalid or has expired",
        );
      }
      const data: InvitationInfo = await res.json();
      setInvitation(data);
      setError(null);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "This invitation is invalid or has expired";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  // Load invitation on mount
  useEffect(() => {
    fetchInvitation();
  }, [fetchInvitation]);

  // Auto-accept for logged-in users with matching email
  useEffect(() => {
    if (
      !authLoading &&
      isLoggedIn &&
      user &&
      invitation &&
      user.email.toLowerCase() === invitation.email.toLowerCase()
    ) {
      handleAcceptExistingUser();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading, isLoggedIn, user, invitation]);

  // Accept as existing user
  const handleAcceptExistingUser = async () => {
    if (!token) return;
    setIsSubmitting(true);
    setFormError("");

    try {
      const res = await fetch(`${API_BASE}/api/invitations/accept/${token}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to accept invitation");
      }
      const data: AcceptResponse = await res.json();
      setAcceptSuccess(data);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to accept invitation";
      setFormError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Form submission for new users
  const handleSubmitNewUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");

    if (!fullName.trim() || fullName.trim().length < 2) {
      setFormError("Full name must be at least 2 characters");
      return;
    }
    if (password.length < 8) {
      setFormError("Password must be at least 8 characters");
      return;
    }
    if (!/[A-Z]/.test(password)) {
      setFormError("Password must contain at least one uppercase letter");
      return;
    }
    if (!/[a-z]/.test(password)) {
      setFormError("Password must contain at least one lowercase letter");
      return;
    }
    if (!/\d/.test(password)) {
      setFormError("Password must contain at least one number");
      return;
    }
    if (password !== confirmPassword) {
      setFormError("Passwords do not match");
      return;
    }
    if (!token) return;

    setIsSubmitting(true);

    try {
      const res = await fetch(`${API_BASE}/api/invitations/accept/${token}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fullName.trim(),
          password,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to create account");
      }
      const data: AcceptResponse = await res.json();
      setAcceptSuccess(data);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to create account";
      setFormError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogoutAndAccept = () => {
    logout();
  };

  const handleContinueToDashboard = () => {
    router.push("/dashboard");
  };

  // Loading state
  if (authLoading || isLoading) {
    return (
      <div className="w-full max-w-md px-4">
        <div className="text-center mb-8">
          <div className="flex justify-center">
            <div className="bg-primary p-3 rounded-xl shadow-lg">
              <Package className="h-10 w-10 text-primary-foreground" />
            </div>
          </div>
          <h1 className="mt-4 text-3xl font-bold">TraceHub</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Container Tracking & Compliance Platform
          </p>
        </div>
        <Card>
          <CardContent className="py-12">
            <div className="flex flex-col items-center">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <p className="mt-4 text-muted-foreground">
                Loading invitation details...
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md px-4">
      {/* Logo and Title */}
      <div className="text-center mb-8">
        <div className="flex justify-center">
          <div className="bg-primary p-3 rounded-xl shadow-lg">
            <Package className="h-10 w-10 text-primary-foreground" />
          </div>
        </div>
        <h1 className="mt-4 text-3xl font-bold">TraceHub</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Container Tracking & Compliance Platform
        </p>
      </div>

      <Card>
        <CardContent className="p-6">
          {/* Error State */}
          {error && (
            <div className="text-center py-8">
              <div className="mx-auto w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center mb-4">
                <XCircle className="w-8 h-8 text-destructive" />
              </div>
              <h2 className="text-xl font-semibold mb-2">Invitation Error</h2>
              <p className="text-muted-foreground mb-6">{error}</p>
              <Button onClick={() => router.push("/")}>
                <LogIn className="w-4 h-4 mr-2" />
                Go to Login
              </Button>
            </div>
          )}

          {/* Success State */}
          {!error && acceptSuccess && (
            <div className="text-center py-8">
              <div className="mx-auto w-16 h-16 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center mb-4">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-xl font-semibold mb-2">
                Welcome to {acceptSuccess.organization_name}!
              </h2>
              <p className="text-muted-foreground mb-6">
                You have successfully joined the organization. You can now
                access shared shipments and documents.
              </p>
              <Button onClick={handleContinueToDashboard}>
                Go to Dashboard
              </Button>
            </div>
          )}

          {/* Email Mismatch State */}
          {!error &&
            !acceptSuccess &&
            invitation &&
            isLoggedIn &&
            user &&
            user.email.toLowerCase() !== invitation.email.toLowerCase() && (
              <div className="text-center py-8">
                <div className="mx-auto w-16 h-16 bg-yellow-100 dark:bg-yellow-900/20 rounded-full flex items-center justify-center mb-4">
                  <AlertCircle className="w-8 h-8 text-yellow-600" />
                </div>
                <h2 className="text-xl font-semibold mb-2">Email Mismatch</h2>
                <p className="text-muted-foreground mb-4">
                  This invitation is for{" "}
                  <span className="font-medium">{invitation.email}</span>, but
                  you are currently logged in as{" "}
                  <span className="font-medium">{user.email}</span>.
                </p>
                <div className="flex flex-col sm:flex-row gap-3 justify-center mt-6">
                  <Button onClick={handleLogoutAndAccept}>
                    <LogOut className="w-4 h-4 mr-2" />
                    Log out and Accept
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handleContinueToDashboard}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}

          {/* Auto-accepting spinner */}
          {!error &&
            !acceptSuccess &&
            invitation &&
            isLoggedIn &&
            user &&
            user.email.toLowerCase() === invitation.email.toLowerCase() &&
            isSubmitting && (
              <div className="text-center py-8">
                <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
                <p className="mt-4 text-muted-foreground">
                  Accepting invitation...
                </p>
              </div>
            )}

          {/* Invitation Details (unauthenticated) */}
          {!error && !acceptSuccess && invitation && !isLoggedIn && (
            <>
              <div className="text-center mb-6">
                <CardTitle className="text-xl">
                  You have been invited!
                </CardTitle>
                {invitation.invited_by_name && (
                  <CardDescription className="mt-1">
                    {invitation.invited_by_name} has invited you to join
                  </CardDescription>
                )}
              </div>

              {/* Organization Info */}
              <div className="bg-muted rounded-lg p-4 mb-6 space-y-3">
                <div className="flex items-center">
                  <Building2 className="w-5 h-5 text-primary mr-2" />
                  <span className="font-medium">
                    {invitation.organization_name}
                  </span>
                </div>
                <div className="flex items-center">
                  <Mail className="w-5 h-5 text-muted-foreground mr-2" />
                  <span className="text-muted-foreground">
                    {invitation.email}
                  </span>
                </div>
                <div className="flex items-start">
                  <Shield className="w-5 h-5 text-muted-foreground mr-2 mt-0.5" />
                  <div>
                    <span className="font-medium">
                      {ROLE_LABELS[invitation.org_role]}
                    </span>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {ROLE_DESCRIPTIONS[invitation.org_role]}
                    </p>
                  </div>
                </div>
              </div>

              {/* Custom Message */}
              {invitation.custom_message && (
                <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 mb-6">
                  <p className="text-sm italic">
                    &quot;{invitation.custom_message}&quot;
                  </p>
                </div>
              )}

              {/* Existing User - Login Required */}
              {!invitation.requires_registration && (
                <div className="text-center">
                  <div className="mb-4">
                    <span className="inline-flex items-center px-3 py-1 rounded-full bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 text-sm">
                      <User className="w-4 h-4 mr-1" />
                      Account exists
                    </span>
                  </div>
                  <p className="text-muted-foreground mb-6">
                    An account already exists for this email. Please log in to
                    accept the invitation.
                  </p>
                  <Button className="w-full" onClick={() => router.push("/")}>
                    <LogIn className="w-4 h-4 mr-2" />
                    Log in to Accept
                  </Button>
                </div>
              )}

              {/* New User - Registration Form */}
              {invitation.requires_registration && (
                <form onSubmit={handleSubmitNewUser} className="space-y-4">
                  <div className="mb-4">
                    <span className="inline-flex items-center px-3 py-1 rounded-full bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 text-sm">
                      <User className="w-4 h-4 mr-1" />
                      Create your account
                    </span>
                  </div>

                  {formError && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{formError}</AlertDescription>
                    </Alert>
                  )}

                  <div className="space-y-2">
                    <Label htmlFor="fullName">Full Name</Label>
                    <Input
                      id="fullName"
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Enter your full name"
                      required
                      disabled={isSubmitting}
                      autoFocus
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Create a password"
                        required
                        autoComplete="new-password"
                        disabled={isSubmitting}
                        className="pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground hover:text-foreground transition-colors"
                        tabIndex={-1}
                        aria-label={
                          showPassword ? "Hide password" : "Show password"
                        }
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                    <PasswordStrength password={password} />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword">Confirm Password</Label>
                    <Input
                      id="confirmPassword"
                      type={showPassword ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Confirm your password"
                      required
                      autoComplete="new-password"
                      disabled={isSubmitting}
                    />
                    {confirmPassword && password !== confirmPassword && (
                      <p className="text-sm text-destructive">
                        Passwords do not match
                      </p>
                    )}
                  </div>

                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full mt-6"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        Creating account...
                      </>
                    ) : (
                      "Accept & Create Account"
                    )}
                  </Button>
                </form>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <p className="mt-8 text-center text-xs text-muted-foreground">
        VIBOTAJ Global Nigeria Ltd
      </p>
    </div>
  );
}
