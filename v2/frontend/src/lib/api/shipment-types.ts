// --- Shipment types (no React/PropelAuth dependencies) ---

export type ShipmentStatus =
  | "draft"
  | "docs_pending"
  | "docs_complete"
  | "in_transit"
  | "arrived"
  | "customs"
  | "delivered"
  | "archived";

export interface Shipment {
  id: string;
  reference: string;
  container_number: string | null;
  status: ShipmentStatus;
  product_type: string | null;
  vessel_name: string | null;
  voyage_number: string | null;
  pol_code: string | null;
  pol_name: string | null;
  pod_code: string | null;
  pod_name: string | null;
  eta: string | null;
  etd: string | null;
  created_at: string;
  updated_at: string;
  organization_id: string;
}

export interface ShipmentListResponse {
  items: Shipment[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface ShipmentListParams {
  status?: ShipmentStatus | "all";
  search?: string;
  limit?: number;
  offset?: number;
}

export interface DashboardStats {
  totalShipments: number;
  docsPending: number;
  inTransit: number;
  complianceRate: number;
  statusBreakdown: { status: ShipmentStatus; count: number }[];
  monthlyVolume: { month: string; count: number }[];
  complianceTrend: { month: string; rate: number }[];
  recentShipments: Shipment[];
}

// --- Stats computation ---

export function computeStats(shipments: Shipment[]): DashboardStats {
  const statusCounts = new Map<ShipmentStatus, number>();
  const monthlyCounts = new Map<string, number>();
  const monthlyCompliant = new Map<string, number>();
  const monthlyTotal = new Map<string, number>();

  for (const s of shipments) {
    statusCounts.set(s.status, (statusCounts.get(s.status) ?? 0) + 1);

    const month = s.created_at.slice(0, 7);
    monthlyCounts.set(month, (monthlyCounts.get(month) ?? 0) + 1);
    monthlyTotal.set(month, (monthlyTotal.get(month) ?? 0) + 1);
    if (
      s.status === "docs_complete" ||
      s.status === "delivered" ||
      s.status === "arrived"
    ) {
      monthlyCompliant.set(month, (monthlyCompliant.get(month) ?? 0) + 1);
    }
  }

  const statusBreakdown = Array.from(statusCounts.entries())
    .map(([status, count]) => ({ status, count }))
    .sort((a, b) => b.count - a.count);

  const now = new Date();
  const months: string[] = [];
  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    months.push(d.toISOString().slice(0, 7));
  }

  const monthlyVolume = months.map((m) => ({
    month: formatMonth(m),
    count: monthlyCounts.get(m) ?? 0,
  }));

  const complianceTrend = months.map((m) => {
    const total = monthlyTotal.get(m) ?? 0;
    const compliant = monthlyCompliant.get(m) ?? 0;
    return {
      month: formatMonth(m),
      rate: total > 0 ? Math.round((compliant / total) * 100) : 0,
    };
  });

  const docsPending = statusCounts.get("docs_pending") ?? 0;
  const inTransit = statusCounts.get("in_transit") ?? 0;
  const compliantCount = shipments.filter(
    (s) =>
      s.status === "docs_complete" ||
      s.status === "delivered" ||
      s.status === "arrived",
  ).length;
  const complianceRate =
    shipments.length > 0
      ? Math.round((compliantCount / shipments.length) * 100)
      : 0;

  const recentShipments = [...shipments]
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    )
    .slice(0, 5);

  return {
    totalShipments: shipments.length,
    docsPending,
    inTransit,
    complianceRate,
    statusBreakdown,
    monthlyVolume,
    complianceTrend,
    recentShipments,
  };
}

export function formatMonth(yyyyMm: string): string {
  const [year, month] = yyyyMm.split("-");
  const monthNames = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
  ];
  const idx = parseInt(month!, 10) - 1;
  return `${monthNames[idx]} ${year}`;
}
