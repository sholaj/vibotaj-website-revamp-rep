import { MapPin, Ship, Clock, AlertTriangle, Navigation } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  EVENT_TYPE_LABELS,
  formatRelativeTime,
  type ContainerEvent,
} from "@/lib/api/tracking-types";

interface LiveStatusCardProps {
  latestEvent: ContainerEvent | null;
  containerNumber: string | null;
  eta: string | null;
  onSyncTracking?: () => void;
  isSyncing?: boolean;
  error?: string | null;
}

function formatDate(iso: string | null): string {
  if (!iso) return "TBD";
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function LiveStatusCard({
  latestEvent,
  containerNumber,
  eta,
  onSyncTracking,
  isSyncing,
  error,
}: LiveStatusCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Navigation className="h-4 w-4" />
          Live Status
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {error && (
          <div className="flex items-start gap-2 rounded-md bg-warning/10 p-3 text-sm">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
            <div>
              <p className="font-medium text-warning">Tracking unavailable</p>
              <p className="text-muted-foreground text-xs">{error}</p>
            </div>
          </div>
        )}

        {latestEvent ? (
          <>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground text-sm">Status</span>
              <Badge variant="secondary">
                {EVENT_TYPE_LABELS[latestEvent.event_type]}
              </Badge>
            </div>

            {latestEvent.vessel_name && (
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground flex items-center gap-1 text-sm">
                  <Ship className="h-3.5 w-3.5" />
                  Vessel
                </span>
                <span className="text-sm font-medium">
                  {latestEvent.vessel_name}
                </span>
              </div>
            )}

            {latestEvent.location_name && (
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground flex items-center gap-1 text-sm">
                  <MapPin className="h-3.5 w-3.5" />
                  Location
                </span>
                <span className="text-sm font-medium">
                  {latestEvent.location_name}
                  {latestEvent.location_code && (
                    <span className="text-muted-foreground ml-1 text-xs">
                      ({latestEvent.location_code})
                    </span>
                  )}
                </span>
              </div>
            )}

            {eta && (
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground flex items-center gap-1 text-sm">
                  <Clock className="h-3.5 w-3.5" />
                  ETA
                </span>
                <span className="text-sm font-medium">{formatDate(eta)}</span>
              </div>
            )}

            <div className="flex items-center justify-between">
              <span className="text-muted-foreground text-sm">
                Last Updated
              </span>
              <span className="text-muted-foreground text-xs">
                {formatRelativeTime(latestEvent.timestamp)}
              </span>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center py-4 text-center">
            <Ship className="text-muted-foreground mb-2 h-8 w-8" />
            <p className="text-muted-foreground text-sm">
              {containerNumber
                ? "No tracking data yet"
                : "No container number assigned"}
            </p>
          </div>
        )}

        {onSyncTracking && (
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={onSyncTracking}
            disabled={isSyncing || !containerNumber}
          >
            {isSyncing ? "Syncing..." : "Sync Live Tracking"}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
