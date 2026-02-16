"use client";

import { useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { PageHeader } from "@/components/domain/page-header";
import { DataTable } from "@/components/domain/data-table";
import { LoadingState } from "@/components/domain/loading-state";
import { ErrorState } from "@/components/domain/error-state";
import { Button } from "@/components/ui/button";
import { shipmentColumns } from "@/components/shipments/shipment-columns";
import { ShipmentStatusFilter } from "@/components/shipments/shipment-status-filter";
import { useShipments } from "@/lib/api/shipments";
import type { ShipmentStatus } from "@/lib/api/shipment-types";

export default function ShipmentsPage() {
  const [statusFilter, setStatusFilter] = useState<ShipmentStatus | "all">(
    "all",
  );
  const { data, isLoading, error, refetch } = useShipments({
    status: statusFilter,
    limit: 100,
  });

  const shipments = data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Shipments"
        description="Manage and track all your shipments."
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Shipments" },
        ]}
        actions={
          <Button asChild>
            <Link href="/shipments/new">
              <Plus className="mr-2 h-4 w-4" />
              New Shipment
            </Link>
          </Button>
        }
      />

      <ShipmentStatusFilter value={statusFilter} onChange={setStatusFilter} />

      {isLoading && <LoadingState variant="table" />}

      {error && (
        <ErrorState
          message="Failed to load shipments."
          onRetry={() => refetch()}
        />
      )}

      {!isLoading && !error && (
        <DataTable
          columns={shipmentColumns}
          data={shipments}
          filterColumn="reference"
          filterPlaceholder="Search by reference..."
          emptyTitle="No shipments found"
          emptyDescription="Create your first shipment to get started."
        />
      )}
    </div>
  );
}
