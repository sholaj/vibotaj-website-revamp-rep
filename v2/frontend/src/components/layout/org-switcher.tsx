"use client";

import { Check, ChevronsUpDown } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { useCurrentOrg } from "@/lib/auth/org-context";

function getOrgInitials(name: string): string {
  return name
    .split(/\s+/)
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function OrgSwitcher() {
  const { org, orgs, switchOrg } = useCurrentOrg();

  if (!org || orgs.length === 0) return null;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="w-full justify-start gap-2 px-2"
          aria-label="Switch organization"
        >
          <Avatar className="h-6 w-6">
            <AvatarFallback className="text-[10px]">
              {getOrgInitials(org.orgName)}
            </AvatarFallback>
          </Avatar>
          <span className="flex-1 truncate text-left text-sm font-medium">
            {org.orgName}
          </span>
          {orgs.length > 1 && (
            <ChevronsUpDown className="text-muted-foreground h-4 w-4 shrink-0" />
          )}
        </Button>
      </DropdownMenuTrigger>
      {orgs.length > 1 && (
        <DropdownMenuContent align="start" className="w-56">
          {orgs.map((o) => (
            <DropdownMenuItem
              key={o.orgId}
              onClick={() => switchOrg(o.orgId)}
              className="gap-2"
            >
              <Avatar className="h-5 w-5">
                <AvatarFallback className="text-[9px]">
                  {getOrgInitials(o.orgName)}
                </AvatarFallback>
              </Avatar>
              <span className="flex-1 truncate">{o.orgName}</span>
              {o.orgId === org.orgId && (
                <Check className="text-primary h-4 w-4 shrink-0" />
              )}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      )}
    </DropdownMenu>
  );
}
