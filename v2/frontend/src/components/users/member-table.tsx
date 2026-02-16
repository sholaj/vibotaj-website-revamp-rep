import { MoreHorizontal, UserPlus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/domain/empty-state";
import { StatusBadge, type Role } from "@/components/domain/status-badge";
import {
  formatLastActive,
  type UserResponse,
} from "@/lib/api/user-types";

interface MemberTableProps {
  users: UserResponse[];
  onInvite?: () => void;
  onChangeRole?: (userId: string, role: string) => void;
  onToggleActive?: (userId: string, isActive: boolean) => void;
  canManage?: boolean;
}

const SYSTEM_ROLE_MAP: Record<string, Role> = {
  admin: "admin",
  compliance_officer: "compliance_officer",
  compliance: "compliance_officer",
  logistics_agent: "logistics",
  logistics: "logistics",
  buyer: "buyer",
  supplier: "supplier",
  viewer: "viewer",
};

function mapToRole(role: string): Role {
  return SYSTEM_ROLE_MAP[role] ?? "viewer";
}

export function MemberTable({
  users,
  onInvite,
  onChangeRole,
  onToggleActive,
  canManage = false,
}: MemberTableProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg">
          Team Members ({users.length})
        </CardTitle>
        {onInvite && canManage && (
          <Button size="sm" onClick={onInvite}>
            <UserPlus className="mr-2 h-4 w-4" />
            Invite Member
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {users.length === 0 ? (
          <EmptyState
            title="No team members"
            description="Invite members to collaborate on shipments and documents."
          />
        ) : (
          <div className="space-y-0">
            {users.map((user) => (
              <div
                key={user.id}
                className="border-border flex items-center justify-between border-b py-3 last:border-0"
              >
                <div className="flex items-center gap-3">
                  <div className="bg-primary/10 text-primary flex h-9 w-9 items-center justify-center rounded-full text-sm font-medium">
                    {user.full_name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">
                        {user.full_name}
                      </span>
                      {!user.is_active && (
                        <Badge variant="outline" className="text-muted-foreground text-xs">
                          Inactive
                        </Badge>
                      )}
                    </div>
                    <p className="text-muted-foreground text-xs">{user.email}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <StatusBadge variant="role" status={mapToRole(user.role)} />
                  <span className="text-muted-foreground hidden text-xs sm:inline">
                    {formatLastActive(user.last_login)}
                  </span>
                  {canManage && (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {onChangeRole && (
                          <>
                            <DropdownMenuItem
                              onClick={() => onChangeRole(user.id, "admin")}
                            >
                              Set as Admin
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => onChangeRole(user.id, "viewer")}
                            >
                              Set as Viewer
                            </DropdownMenuItem>
                          </>
                        )}
                        {onToggleActive && (
                          <DropdownMenuItem
                            onClick={() => onToggleActive(user.id, !user.is_active)}
                          >
                            {user.is_active ? "Deactivate" : "Activate"}
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
