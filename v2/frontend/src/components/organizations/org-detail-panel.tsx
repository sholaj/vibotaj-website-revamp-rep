import { Building2, Mail, Phone, Users } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  ORG_TYPE_LABELS,
  ORG_STATUS_LABELS,
  ORG_ROLE_LABELS,
  MEMBERSHIP_STATUS_LABELS,
  getMemberDisplayName,
  type OrgDetail,
  type Member,
} from "@/lib/api/user-types";

interface OrgDetailPanelProps {
  org: OrgDetail | null;
  members: Member[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function OrgDetailPanel({
  org,
  members,
  open,
  onOpenChange,
}: OrgDetailPanelProps) {
  if (!org) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            {org.name}
          </SheetTitle>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Org Info */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Badge variant="secondary">{ORG_TYPE_LABELS[org.type]}</Badge>
              <Badge variant="outline">{ORG_STATUS_LABELS[org.status]}</Badge>
            </div>

            {org.contact_email && (
              <div className="text-muted-foreground flex items-center gap-2 text-sm">
                <Mail className="h-4 w-4" />
                {org.contact_email}
              </div>
            )}

            {org.contact_phone && (
              <div className="text-muted-foreground flex items-center gap-2 text-sm">
                <Phone className="h-4 w-4" />
                {org.contact_phone}
              </div>
            )}

            <div className="text-muted-foreground flex items-center gap-4 text-sm">
              {org.member_count != null && (
                <span className="flex items-center gap-1">
                  <Users className="h-4 w-4" />
                  {org.member_count} members
                </span>
              )}
              {org.shipment_count != null && (
                <span>{org.shipment_count} shipments</span>
              )}
            </div>
          </div>

          <Separator />

          {/* Members list */}
          <div>
            <h3 className="mb-3 text-sm font-medium">
              Members ({members.length})
            </h3>
            {members.length === 0 ? (
              <p className="text-muted-foreground text-sm">No members found.</p>
            ) : (
              <div className="space-y-2">
                {members.map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center justify-between rounded-md border p-2"
                  >
                    <div>
                      <p className="text-sm font-medium">
                        {getMemberDisplayName(member)}
                      </p>
                      {member.email && (
                        <p className="text-muted-foreground text-xs">
                          {member.email}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs">
                        {ORG_ROLE_LABELS[member.org_role]}
                      </Badge>
                      {member.status !== "active" && (
                        <Badge variant="outline" className="text-xs">
                          {MEMBERSHIP_STATUS_LABELS[member.status]}
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
