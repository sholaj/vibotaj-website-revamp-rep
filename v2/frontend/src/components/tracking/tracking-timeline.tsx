import {
  Anchor,
  ArrowRightLeft,
  Box,
  CheckCircle,
  Clock,
  MapPin,
  Ship,
  Shield,
  Truck,
  type LucideIcon,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/domain/empty-state";
import {
  EVENT_TYPE_LABELS,
  formatRelativeTime,
  type ContainerEvent,
  type ContainerEventType,
} from "@/lib/api/tracking-types";

const EVENT_ICONS: Record<ContainerEventType, LucideIcon> = {
  booking_confirmed: Clock,
  gate_in: Box,
  loaded: Anchor,
  departed: Ship,
  transshipment: ArrowRightLeft,
  arrived: MapPin,
  discharged: Anchor,
  gate_out: Box,
  delivered: CheckCircle,
  customs_hold: Shield,
  customs_released: Shield,
  empty_return: Truck,
  unknown: Clock,
};

interface TrackingTimelineProps {
  events: ContainerEvent[];
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function TrackingTimeline({ events }: TrackingTimelineProps) {
  const sorted = [...events].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">
          Tracking ({events.length} events)
        </CardTitle>
      </CardHeader>
      <CardContent>
        {sorted.length === 0 ? (
          <EmptyState
            icon={Ship}
            title="No tracking events"
            description="Tracking data will appear once the container is in transit."
          />
        ) : (
          <div className="relative space-y-0">
            {sorted.map((event, index) => {
              const Icon = EVENT_ICONS[event.event_type];
              const isLatest = index === 0;

              return (
                <div key={event.id} className="relative flex gap-4 pb-6">
                  {/* Vertical line */}
                  {index < sorted.length - 1 && (
                    <div className="bg-border absolute left-[15px] top-8 h-full w-px" />
                  )}

                  {/* Icon */}
                  <div
                    className={`relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                      isLatest
                        ? "bg-primary text-primary-foreground ring-primary/20 ring-4"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                  </div>

                  {/* Content */}
                  <div className="flex-1 pt-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">
                        {EVENT_TYPE_LABELS[event.event_type]}
                      </span>
                      {isLatest && (
                        <Badge variant="secondary" className="text-xs">
                          Latest
                        </Badge>
                      )}
                    </div>
                    <div className="text-muted-foreground mt-0.5 text-xs">
                      {formatDate(event.timestamp)} ({formatRelativeTime(event.timestamp)})
                    </div>
                    {event.location_name && (
                      <div className="text-muted-foreground mt-0.5 flex items-center gap-1 text-xs">
                        <MapPin className="h-3 w-3" />
                        {event.location_name}
                        {event.location_code && (
                          <span className="text-muted-foreground/60">
                            ({event.location_code})
                          </span>
                        )}
                      </div>
                    )}
                    {event.vessel_name && (
                      <div className="text-muted-foreground mt-0.5 flex items-center gap-1 text-xs">
                        <Ship className="h-3 w-3" />
                        {event.vessel_name}
                        {event.voyage_number && ` / ${event.voyage_number}`}
                      </div>
                    )}
                    {event.description && (
                      <p className="text-muted-foreground mt-1 text-xs">
                        {event.description}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
