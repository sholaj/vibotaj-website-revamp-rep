import { Package, BarChart3, Users, Building2 } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
} from "@/components/ui/sidebar";

const navigation = [
  { name: "Shipments", href: "/shipments", icon: Package },
  { name: "Dashboard", href: "/dashboard", icon: BarChart3 },
  { name: "Users", href: "/users", icon: Users },
  { name: "Organizations", href: "/organizations", icon: Building2 },
];

export function AppSidebar() {
  return (
    <Sidebar>
      <SidebarHeader className="border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <Package className="text-primary h-6 w-6" />
          <span className="text-lg font-bold">TraceHub</span>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigation.map((item) => (
                <SidebarMenuItem key={item.name}>
                  <SidebarMenuButton asChild>
                    <a href={item.href}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.name}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t px-4 py-3">
        <p className="text-muted-foreground text-xs">
          TraceHub v2 &mdash; Container Tracking &amp; Compliance
        </p>
      </SidebarFooter>
    </Sidebar>
  );
}
