import { Building2, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/domain/empty-state";
import {
  ORG_TYPE_LABELS,
  ORG_STATUS_LABELS,
  type OrgListItem,
} from "@/lib/api/user-types";

interface OrgTableProps {
  organizations: OrgListItem[];
  onSelect?: (orgId: string) => void;
}

const STATUS_CLASSES: Record<string, string> = {
  active:
    "bg-success/10 text-success border-success/20",
  suspended:
    "bg-destructive/10 text-destructive border-destructive/20",
  pending_setup:
    "bg-warning/10 text-warning border-warning/20",
};

export function OrgTable({ organizations, onSelect }: OrgTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">
          Organizations ({organizations.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        {organizations.length === 0 ? (
          <EmptyState
            icon={Building2}
            title="No organizations"
            description="Organizations will appear here once configured."
          />
        ) : (
          <div className="space-y-0">
            {organizations.map((org) => (
              <div
                key={org.id}
                className="border-border flex cursor-pointer items-center justify-between border-b py-3 transition-colors hover:bg-accent/50 last:border-0"
                onClick={() => onSelect?.(org.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") onSelect?.(org.id);
                }}
              >
                <div className="flex items-center gap-3">
                  <div className="bg-muted flex h-9 w-9 items-center justify-center rounded-lg">
                    <Building2 className="text-muted-foreground h-5 w-5" />
                  </div>
                  <div>
                    <span className="text-sm font-medium">{org.name}</span>
                    <div className="mt-0.5 flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs">
                        {ORG_TYPE_LABELS[org.type]}
                      </Badge>
                      <Badge
                        variant="outline"
                        className={`text-xs ${STATUS_CLASSES[org.status] ?? ""}`}
                      >
                        {ORG_STATUS_LABELS[org.status]}
                      </Badge>
                    </div>
                  </div>
                </div>

                <div className="text-muted-foreground flex items-center gap-1 text-sm">
                  <Users className="h-4 w-4" />
                  {org.member_count}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
