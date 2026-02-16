import {
  Archive,
  CheckCircle,
  Clock,
  Eye,
  FileEdit,
  MapPin,
  Ship,
  Shield,
  XCircle,
  AlertTriangle,
  type LucideIcon,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

// --- Shipment statuses ---

export type ShipmentStatus =
  | "draft"
  | "docs_pending"
  | "docs_complete"
  | "in_transit"
  | "arrived"
  | "customs"
  | "delivered"
  | "archived";

const SHIPMENT_CONFIG: Record<
  ShipmentStatus,
  { label: string; icon: LucideIcon; className: string }
> = {
  draft: {
    label: "Draft",
    icon: FileEdit,
    className: "bg-info/10 text-info border-info/20",
  },
  docs_pending: {
    label: "Docs Pending",
    icon: Clock,
    className: "bg-warning/10 text-warning border-warning/20",
  },
  docs_complete: {
    label: "Docs Complete",
    icon: CheckCircle,
    className: "bg-success/10 text-success border-success/20",
  },
  in_transit: {
    label: "In Transit",
    icon: Ship,
    className: "bg-info/10 text-info border-info/20",
  },
  arrived: {
    label: "Arrived",
    icon: MapPin,
    className: "bg-success/10 text-success border-success/20",
  },
  customs: {
    label: "At Customs",
    icon: Shield,
    className: "bg-warning/10 text-warning border-warning/20",
  },
  delivered: {
    label: "Delivered",
    icon: CheckCircle,
    className: "bg-success/10 text-success border-success/20",
  },
  archived: {
    label: "Archived",
    icon: Archive,
    className: "bg-muted text-muted-foreground border-muted",
  },
};

// --- Document statuses ---

export type DocumentStatus =
  | "pending"
  | "uploaded"
  | "under_review"
  | "approved"
  | "rejected"
  | "expired";

const DOCUMENT_CONFIG: Record<
  DocumentStatus,
  { label: string; icon: LucideIcon; className: string }
> = {
  pending: {
    label: "Pending",
    icon: Clock,
    className: "bg-muted text-muted-foreground border-muted",
  },
  uploaded: {
    label: "Uploaded",
    icon: Clock,
    className: "bg-warning/10 text-warning border-warning/20",
  },
  under_review: {
    label: "Under Review",
    icon: Eye,
    className: "bg-info/10 text-info border-info/20",
  },
  approved: {
    label: "Approved",
    icon: CheckCircle,
    className: "bg-success/10 text-success border-success/20",
  },
  rejected: {
    label: "Rejected",
    icon: XCircle,
    className: "bg-destructive/10 text-destructive border-destructive/20",
  },
  expired: {
    label: "Expired",
    icon: AlertTriangle,
    className: "bg-warning/10 text-warning border-warning/20",
  },
};

// --- Role badges ---

export type Role =
  | "admin"
  | "compliance_officer"
  | "logistics"
  | "buyer"
  | "supplier"
  | "viewer";

const ROLE_CONFIG: Record<Role, { label: string; className: string }> = {
  admin: {
    label: "Admin",
    className:
      "bg-purple-100 text-purple-700 border-purple-200 dark:bg-purple-900/30 dark:text-purple-400 dark:border-purple-800",
  },
  compliance_officer: {
    label: "Compliance",
    className:
      "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800",
  },
  logistics: {
    label: "Logistics",
    className:
      "bg-teal-100 text-teal-700 border-teal-200 dark:bg-teal-900/30 dark:text-teal-400 dark:border-teal-800",
  },
  buyer: {
    label: "Buyer",
    className:
      "bg-green-100 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800",
  },
  supplier: {
    label: "Supplier",
    className:
      "bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-900/30 dark:text-orange-400 dark:border-orange-800",
  },
  viewer: {
    label: "Viewer",
    className:
      "bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-700",
  },
};

// --- Component ---

type StatusBadgeProps =
  | { variant: "shipment"; status: ShipmentStatus }
  | { variant: "document"; status: DocumentStatus }
  | { variant: "role"; status: Role };

export function StatusBadge(props: StatusBadgeProps) {
  if (props.variant === "shipment") {
    const config = SHIPMENT_CONFIG[props.status];
    const Icon = config.icon;
    return (
      <Badge variant="outline" className={cn("gap-1", config.className)}>
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  }

  if (props.variant === "document") {
    const config = DOCUMENT_CONFIG[props.status];
    const Icon = config.icon;
    return (
      <Badge variant="outline" className={cn("gap-1", config.className)}>
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  }

  // role
  const config = ROLE_CONFIG[props.status];
  return (
    <Badge variant="outline" className={cn(config.className)}>
      {config.label}
    </Badge>
  );
}
