"use client";

import { useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageHeader } from "@/components/domain/page-header";
import { LoadingState } from "@/components/domain/loading-state";
import { ErrorState } from "@/components/domain/error-state";
import { ShipmentHeader } from "@/components/shipments/shipment-header";
import { ShipmentInfo } from "@/components/shipments/shipment-info";
import { DocumentList } from "@/components/documents/document-list";
import { DocumentUploadModal } from "@/components/documents/document-upload-modal";
import { DocumentReviewPanel } from "@/components/documents/document-review-panel";
import { TrackingTimeline } from "@/components/tracking/tracking-timeline";
import { LiveStatusCard } from "@/components/tracking/live-status-card";
import { ComplianceStatus } from "@/components/compliance/compliance-status";
import { EudrStatusCard } from "@/components/compliance/eudr-status-card";
import { useShipmentDetail } from "@/lib/api/documents";
import {
  useShipmentDocuments,
  useShipmentEvents,
  useUploadDocument,
  useApproveDocument,
  useRejectDocument,
  useDeleteDocument,
} from "@/lib/api/documents";
import { isEudrRequired } from "@/lib/api/shipment-types";
import {
  useContainerEventsRealtime,
  useShipmentRealtime,
  useRefreshTracking,
} from "@/lib/supabase/use-realtime";
import { useCurrentOrg } from "@/lib/auth/org-context";
import type { Document } from "@/lib/api/document-types";
import type { ContainerEvent } from "@/lib/api/tracking-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function ShipmentDetailPage() {
  const params = useParams<{ id: string }>();
  const shipmentId = params.id;
  const { role } = useCurrentOrg();

  const {
    data: shipment,
    isLoading: shipmentLoading,
    error: shipmentError,
    refetch: refetchShipment,
  } = useShipmentDetail(shipmentId);

  const {
    data: docsData,
    isLoading: docsLoading,
    error: docsError,
  } = useShipmentDocuments(shipmentId);

  const {
    data: eventsData,
    isLoading: eventsLoading,
  } = useShipmentEvents(shipmentId);

  const uploadMutation = useUploadDocument(shipmentId);
  const approveMutation = useApproveDocument(shipmentId);
  const rejectMutation = useRejectDocument(shipmentId);
  const deleteMutation = useDeleteDocument(shipmentId);

  const [uploadOpen, setUploadOpen] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [newEventIds, setNewEventIds] = useState<Set<string>>(new Set());
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);

  const canApprove = role === "admin" || role === "compliance_officer";

  // Realtime subscriptions
  const handleNewEvent = useCallback((event: ContainerEvent) => {
    setNewEventIds((prev) => new Set([...prev, event.id]));
    // Clear animation after 5 seconds
    setTimeout(() => {
      setNewEventIds((prev) => {
        const next = new Set(prev);
        next.delete(event.id);
        return next;
      });
    }, 5000);
  }, []);

  useContainerEventsRealtime(shipmentId, handleNewEvent);
  useShipmentRealtime(shipmentId);

  const { refresh } = useRefreshTracking(shipmentId);

  const handleRefreshTracking = useCallback(async () => {
    setIsRefreshing(true);
    setRefreshError(null);
    try {
      await refresh();
    } catch {
      setRefreshError("Could not refresh tracking. The carrier may not have data for this container yet.");
    } finally {
      setIsRefreshing(false);
    }
  }, [refresh]);

  const handleDownload = (doc: Document) => {
    if (doc.file_path) {
      window.open(`${API_BASE}/api/documents/${doc.id}/download`, "_blank");
    }
  };

  if (shipmentLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Loading..." />
        <LoadingState variant="detail" />
      </div>
    );
  }

  if (shipmentError || !shipment) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Shipment"
          breadcrumbs={[
            { label: "Dashboard", href: "/dashboard" },
            { label: "Shipments", href: "/shipments" },
            { label: "Not Found" },
          ]}
        />
        <ErrorState
          message={
            shipmentError?.message === "Shipment not found"
              ? "This shipment does not exist or you don't have access."
              : "Failed to load shipment details."
          }
          onRetry={() => refetchShipment()}
        />
      </div>
    );
  }

  const documents = docsData?.documents ?? [];
  const missingTypes = docsData?.summary.missing_types ?? [];
  const events = eventsData?.events ?? [];
  const latestEvent = events.length > 0
    ? [...events].sort(
        (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
      )[0] ?? null
    : null;

  return (
    <div className="space-y-6">
      <PageHeader
        title=""
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Shipments", href: "/shipments" },
          { label: shipment.reference },
        ]}
      />

      <ShipmentHeader
        shipment={shipment}
        onRefreshTracking={handleRefreshTracking}
        isRefreshing={isRefreshing}
        onDownloadAuditPack={() => {
          window.open(
            `${API_BASE}/api/shipments/${shipmentId}/audit-pack`,
            "_blank",
          );
        }}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Main content */}
        <div className="space-y-6 lg:col-span-2">
          <ShipmentInfo shipment={shipment} />

          <Tabs defaultValue="documents">
            <TabsList>
              <TabsTrigger value="documents">
                Documents ({documents.length})
              </TabsTrigger>
              <TabsTrigger value="tracking">
                Tracking ({events.length})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="documents" className="mt-4">
              {docsLoading ? (
                <LoadingState variant="table" />
              ) : docsError ? (
                <ErrorState message="Failed to load documents." />
              ) : (
                <DocumentList
                  documents={documents}
                  missingTypes={missingTypes}
                  onUpload={() => setUploadOpen(true)}
                  onSelect={(doc) => {
                    setSelectedDoc(doc);
                    setReviewOpen(true);
                  }}
                  onDownload={handleDownload}
                />
              )}
            </TabsContent>

            <TabsContent value="tracking" className="mt-4">
              {eventsLoading ? (
                <LoadingState variant="table" />
              ) : (
                <TrackingTimeline events={events} newEventIds={newEventIds} />
              )}
            </TabsContent>
          </Tabs>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <LiveStatusCard
            latestEvent={latestEvent}
            containerNumber={shipment.container_number}
            eta={shipment.eta}
            onSyncTracking={handleRefreshTracking}
            isSyncing={isRefreshing}
            error={refreshError}
          />

          {docsData?.summary && (
            <ComplianceStatus summary={docsData.summary} />
          )}

          {isEudrRequired(shipment) && (
            <EudrStatusCard shipment={shipment} />
          )}
        </div>
      </div>

      {/* Upload Modal */}
      <DocumentUploadModal
        open={uploadOpen}
        onOpenChange={setUploadOpen}
        isUploading={uploadMutation.isPending}
        onUpload={(file, type, ref) => {
          uploadMutation.mutate(
            { file, documentType: type, referenceNumber: ref },
            { onSuccess: () => setUploadOpen(false) },
          );
        }}
      />

      {/* Review Panel */}
      <DocumentReviewPanel
        document={selectedDoc}
        open={reviewOpen}
        onOpenChange={setReviewOpen}
        canApprove={canApprove}
        isApproving={approveMutation.isPending}
        isRejecting={rejectMutation.isPending}
        isDeleting={deleteMutation.isPending}
        onApprove={(docId, notes) => {
          approveMutation.mutate(
            { documentId: docId, notes },
            {
              onSuccess: () => {
                setReviewOpen(false);
                setSelectedDoc(null);
              },
            },
          );
        }}
        onReject={(docId, reason) => {
          rejectMutation.mutate(
            { documentId: docId, reason },
            {
              onSuccess: () => {
                setReviewOpen(false);
                setSelectedDoc(null);
              },
            },
          );
        }}
        onDelete={(docId, reason) => {
          deleteMutation.mutate(
            { documentId: docId, reason },
            {
              onSuccess: () => {
                setReviewOpen(false);
                setSelectedDoc(null);
              },
            },
          );
        }}
        onDownload={handleDownload}
      />
    </div>
  );
}
