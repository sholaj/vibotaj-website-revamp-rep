export const dynamic = "force-dynamic";

import { SidebarProvider } from "@/components/ui/sidebar";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { Header } from "@/components/layout/header";
import { MainContent } from "@/components/layout/main-content";
import { AuthProvider } from "@/lib/auth/provider";
import { OrgProvider } from "@/lib/auth/org-context";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <OrgProvider>
        <TooltipProvider>
          <SidebarProvider>
            <AppSidebar />
            <div className="flex min-h-screen flex-1 flex-col">
              <Header />
              <MainContent>{children}</MainContent>
            </div>
          </SidebarProvider>
        </TooltipProvider>
      </OrgProvider>
    </AuthProvider>
  );
}
