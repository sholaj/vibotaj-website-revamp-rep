"use client";

import { useState } from "react";
import { Users, Plus, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

interface InviteTeamStepProps {
  orgId: string;
  onNext: () => void;
  onBack: () => void;
}

interface PendingInvite {
  email: string;
  role: string;
}

const ROLES = [
  { value: "admin", label: "Admin" },
  { value: "manager", label: "Manager" },
  { value: "member", label: "Member" },
  { value: "viewer", label: "Viewer" },
];

export function InviteTeamStep({
  orgId: _orgId,
  onNext,
  onBack,
}: InviteTeamStepProps) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("member");
  const [invites, setInvites] = useState<PendingInvite[]>([]);
  const [isSending, setIsSending] = useState(false);

  const isValidEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  const handleAddInvite = () => {
    if (!isValidEmail) return;
    if (invites.some((i) => i.email === email)) return;
    setInvites([...invites, { email, role }]);
    setEmail("");
    setRole("member");
  };

  const handleRemoveInvite = (emailToRemove: string) => {
    setInvites(invites.filter((i) => i.email !== emailToRemove));
  };

  const handleSendInvites = async () => {
    if (invites.length === 0) {
      onNext();
      return;
    }

    setIsSending(true);
    // Invites will be sent when properly wired — for now just proceed
    // TODO: Wire to actual invitation API
    setTimeout(() => {
      setIsSending(false);
      onNext();
    }, 500);
  };

  return (
    <div className="space-y-6 py-4">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 bg-primary/10 rounded-full flex items-center justify-center">
          <Users className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-xl font-semibold">Invite Your Team</h2>
          <p className="text-sm text-muted-foreground">
            Add team members to collaborate on shipments
          </p>
        </div>
      </div>

      {/* Add invite form */}
      <div className="flex gap-2">
        <div className="flex-1">
          <Label htmlFor="invite-email" className="sr-only">
            Email
          </Label>
          <Input
            id="invite-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="colleague@company.com"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleAddInvite();
              }
            }}
          />
        </div>
        <Select value={role} onValueChange={setRole}>
          <SelectTrigger className="w-32">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {ROLES.map((r) => (
              <SelectItem key={r.value} value={r.value}>
                {r.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          type="button"
          variant="outline"
          size="icon"
          onClick={handleAddInvite}
          disabled={!isValidEmail}
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {/* Pending invites list */}
      {invites.length > 0 && (
        <div className="space-y-2">
          {invites.map((invite) => (
            <div
              key={invite.email}
              className="flex items-center justify-between rounded-md border px-3 py-2"
            >
              <div className="flex items-center gap-2">
                <span className="text-sm">{invite.email}</span>
                <Badge variant="secondary" className="text-xs">
                  {invite.role}
                </Badge>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={() => handleRemoveInvite(invite.email)}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>
      )}

      {invites.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-4">
          No invites added yet. You can always invite team members later.
        </p>
      )}

      <div className="flex gap-3 pt-2">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button className="flex-1" onClick={handleSendInvites} disabled={isSending}>
          {isSending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              Sending...
            </>
          ) : invites.length > 0 ? (
            `Send ${invites.length} Invite${invites.length > 1 ? "s" : ""} & Continue`
          ) : (
            "Skip & Continue"
          )}
        </Button>
      </div>
    </div>
  );
}
