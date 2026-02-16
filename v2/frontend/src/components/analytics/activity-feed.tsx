import { Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/domain/empty-state";
import {
  formatActivityTime,
  getActionLabel,
  type ActivityItem,
} from "@/lib/api/analytics-types";

interface ActivityFeedProps {
  activities: ActivityItem[];
}

export function ActivityFeed({ activities }: ActivityFeedProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Activity className="h-5 w-5" />
          Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        {activities.length === 0 ? (
          <EmptyState
            icon={Activity}
            title="No recent activity"
            description="Activity will appear here as users interact with the system."
          />
        ) : (
          <div className="space-y-1">
            {activities.map((item) => (
              <div
                key={item.id}
                className="border-border flex items-start gap-3 border-b py-3 last:border-0"
              >
                <div className="bg-muted flex h-8 w-8 shrink-0 items-center justify-center rounded-full">
                  <Activity className="text-muted-foreground h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm">
                    <span className="font-medium">{item.username}</span>{" "}
                    {getActionLabel(item.action)}
                    {item.resource_type && (
                      <span className="text-muted-foreground">
                        {" "}
                        ({item.resource_type})
                      </span>
                    )}
                  </p>
                  <p className="text-muted-foreground mt-0.5 text-xs">
                    {formatActivityTime(item.timestamp)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
