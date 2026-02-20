import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const version = process.env.npm_package_version ?? "0.1.0";
const environment = process.env.NODE_ENV;

export default function HealthPage() {
  return (
    <div className="flex flex-1 items-start justify-center pt-16">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">TraceHub v2</CardTitle>
          <p className="text-muted-foreground text-sm">
            Container Tracking &amp; Compliance Platform
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground text-sm font-medium">
              Status
            </span>
            <Badge
              variant="default"
              className="bg-success text-success-foreground"
            >
              Healthy
            </Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground text-sm font-medium">
              Version
            </span>
            <span className="font-mono text-sm">{version}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground text-sm font-medium">
              Environment
            </span>
            <Badge variant="outline">{environment}</Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground text-sm font-medium">
              Stack
            </span>
            <span className="text-muted-foreground text-sm">
              Next.js 15 + Tailwind v4 + Shadcn
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
