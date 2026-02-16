import { Package } from "lucide-react";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { UserMenu } from "./user-menu";

export function Header() {
  return (
    <header className="bg-card flex h-16 shrink-0 items-center border-b px-4">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mx-4 h-6" />

      {/* Brand */}
      <div className="flex items-center gap-2">
        <Package className="text-primary h-6 w-6" />
        <span className="text-lg font-bold">TraceHub</span>
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Theme toggle */}
      <ThemeToggle />

      {/* User menu */}
      <UserMenu />
    </header>
  );
}
