import { Activity, AlertTriangle, Ship, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TrackingStats } from "@/lib/api/analytics-types";

interface TrackingStatsCardProps {
  stats: TrackingStats;
}

function StatRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-muted-foreground flex items-center gap-2 text-sm">
        <Icon className="h-4 w-4" />
        {label}
      </span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );
}

export function TrackingStatsCard({ stats }: TrackingStatsCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Activity className="h-5 w-5" />
          Tracking Stats
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <StatRow icon={Activity} label="Events (24h)" value={stats.recent_events_24h} />
        <StatRow icon={Ship} label="Containers tracked" value={stats.containers_tracked} />
        <StatRow
          icon={AlertTriangle}
          label="Delays detected"
          value={stats.delays_detected}
        />
        <StatRow
          icon={Clock}
          label="Avg delay"
          value={
            stats.avg_delay_hours > 0
              ? `${stats.avg_delay_hours.toFixed(1)}h`
              : "None"
          }
        />
        <StatRow icon={Activity} label="Total events" value={stats.total_events} />
      </CardContent>
    </Card>
  );
}
