import Link from "next/link";
import { ArrowLeft, Download, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/domain/status-badge";
import type { ShipmentDetail } from "@/lib/api/shipment-types";
import type { ShipmentStatus as BadgeShipmentStatus } from "@/components/domain/status-badge";

interface ShipmentHeaderProps {
  shipment: ShipmentDetail;
  onRefreshTracking?: () => void;
  onDownloadAuditPack?: () => void;
  isRefreshing?: boolean;
}

export function ShipmentHeader({
  shipment,
  onRefreshTracking,
  onDownloadAuditPack,
  isRefreshing,
}: ShipmentHeaderProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/shipments">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{shipment.reference}</h1>
            <StatusBadge
              variant="shipment"
              status={shipment.status as BadgeShipmentStatus}
            />
          </div>
          {shipment.container_number && (
            <p className="text-muted-foreground mt-1 font-mono text-sm">
              {shipment.container_number}
            </p>
          )}
        </div>
      </div>
      <div className="flex gap-2">
        {onRefreshTracking && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRefreshTracking}
            disabled={isRefreshing}
          >
            <RefreshCw
              className={`mr-2 h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`}
            />
            Refresh Tracking
          </Button>
        )}
        {onDownloadAuditPack && (
          <Button size="sm" onClick={onDownloadAuditPack}>
            <Download className="mr-2 h-4 w-4" />
            Audit Pack
          </Button>
        )}
      </div>
    </div>
  );
}
