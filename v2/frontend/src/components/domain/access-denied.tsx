import { ShieldAlert } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export function AccessDenied() {
  return (
    <Card>
      <CardContent className="flex flex-col items-center py-12 text-center">
        <ShieldAlert className="text-muted-foreground mb-4 h-12 w-12" />
        <h3 className="text-lg font-medium">Access Denied</h3>
        <p className="text-muted-foreground mt-2 max-w-sm">
          You do not have permission to view this page. Contact your organization
          admin for access.
        </p>
      </CardContent>
    </Card>
  );
}
