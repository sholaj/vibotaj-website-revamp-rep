import { Mail, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ORG_ROLE_LABELS,
  INVITATION_STATUS_LABELS,
  isInvitationActionable,
  type Invitation,
} from "@/lib/api/user-types";

interface PendingInvitationsProps {
  invitations: Invitation[];
  onRevoke?: (invitationId: string) => void;
  isRevoking?: boolean;
}

export function PendingInvitations({
  invitations,
  onRevoke,
  isRevoking = false,
}: PendingInvitationsProps) {
  const pending = invitations.filter((inv) => inv.status === "pending");

  if (pending.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Mail className="h-5 w-5" />
          Pending Invitations ({pending.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-0">
          {pending.map((inv) => (
            <div
              key={inv.id}
              className="border-border flex items-center justify-between border-b py-3 last:border-0"
            >
              <div>
                <p className="text-sm font-medium">{inv.email}</p>
                <div className="mt-0.5 flex items-center gap-2">
                  <Badge variant="secondary" className="text-xs">
                    {ORG_ROLE_LABELS[inv.org_role]}
                  </Badge>
                  <span className="text-muted-foreground text-xs">
                    Expires{" "}
                    {new Date(inv.expires_at).toLocaleDateString("en-GB", {
                      day: "numeric",
                      month: "short",
                    })}
                  </span>
                </div>
              </div>
              {onRevoke && isInvitationActionable(inv) && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onRevoke(inv.id)}
                  disabled={isRevoking}
                >
                  <X className="mr-1 h-4 w-4" />
                  Revoke
                </Button>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
