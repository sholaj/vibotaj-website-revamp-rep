"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCurrentOrg } from "@/lib/auth/org-context";
import type {
  DocumentType,
  ShipmentDocumentsResponse,
} from "./document-types";
import type { ShipmentEventsResponse } from "./tracking-types";
import type { ShipmentDetail } from "./shipment-types";

// Re-export types for convenience
export type {
  Document,
  DocumentType,
  DocumentStatus,
  DocumentSummary,
  ValidationIssue,
  ShipmentDocumentsResponse,
} from "./document-types";
export {
  DOCUMENT_TYPE_LABELS,
  getComplianceProgress,
  isDocumentComplete,
} from "./document-types";

export type {
  ContainerEvent,
  ContainerEventType,
  ShipmentEventsResponse,
} from "./tracking-types";
export { EVENT_TYPE_LABELS, formatRelativeTime } from "./tracking-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function authHeaders(orgId: string): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-Organization-Id": orgId,
  };
}

// --- Shipment Detail ---

async function fetchShipmentDetail(
  orgId: string,
  shipmentId: string,
): Promise<ShipmentDetail> {
  const res = await fetch(`${API_BASE}/api/shipments/${shipmentId}`, {
    headers: authHeaders(orgId),
  });
  if (res.status === 404) throw new Error("Shipment not found");
  if (!res.ok) throw new Error(`Failed to fetch shipment: ${res.status}`);
  return res.json() as Promise<ShipmentDetail>;
}

export function useShipmentDetail(shipmentId: string) {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["shipment", orgId, shipmentId],
    queryFn: () => fetchShipmentDetail(orgId!, shipmentId),
    enabled: !!orgId && !!shipmentId,
    staleTime: 30_000,
  });
}

// --- Documents ---

async function fetchShipmentDocuments(
  orgId: string,
  shipmentId: string,
): Promise<ShipmentDocumentsResponse> {
  const res = await fetch(
    `${API_BASE}/api/shipments/${shipmentId}/documents`,
    { headers: authHeaders(orgId) },
  );
  if (!res.ok) throw new Error(`Failed to fetch documents: ${res.status}`);
  return res.json() as Promise<ShipmentDocumentsResponse>;
}

export function useShipmentDocuments(shipmentId: string) {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["shipment-documents", orgId, shipmentId],
    queryFn: () => fetchShipmentDocuments(orgId!, shipmentId),
    enabled: !!orgId && !!shipmentId,
    staleTime: 30_000,
  });
}

// --- Tracking Events ---

async function fetchShipmentEvents(
  orgId: string,
  shipmentId: string,
): Promise<ShipmentEventsResponse> {
  const res = await fetch(`${API_BASE}/api/shipments/${shipmentId}/events`, {
    headers: authHeaders(orgId),
  });
  if (!res.ok) throw new Error(`Failed to fetch events: ${res.status}`);
  return res.json() as Promise<ShipmentEventsResponse>;
}

export function useShipmentEvents(shipmentId: string) {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["shipment-events", orgId, shipmentId],
    queryFn: () => fetchShipmentEvents(orgId!, shipmentId),
    enabled: !!orgId && !!shipmentId,
    staleTime: 60_000,
  });
}

// --- Mutations ---

export function useUploadDocument(shipmentId: string) {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      file,
      documentType,
      referenceNumber,
    }: {
      file: File;
      documentType: DocumentType;
      referenceNumber?: string;
    }) => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("document_type", documentType);
      formData.append("shipment_id", shipmentId);
      if (referenceNumber) formData.append("reference_number", referenceNumber);

      const res = await fetch(`${API_BASE}/api/documents/upload`, {
        method: "POST",
        headers: { "X-Organization-Id": orgId! },
        body: formData,
      });
      if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
      return res.json();
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["shipment-documents", orgId, shipmentId],
      });
    },
  });
}

export function useApproveDocument(shipmentId: string) {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      documentId,
      notes,
    }: {
      documentId: string;
      notes?: string;
    }) => {
      const res = await fetch(
        `${API_BASE}/api/documents/${documentId}/approve`,
        {
          method: "POST",
          headers: authHeaders(orgId!),
          body: JSON.stringify({ notes }),
        },
      );
      if (!res.ok) throw new Error(`Approval failed: ${res.status}`);
      return res.json();
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["shipment-documents", orgId, shipmentId],
      });
    },
  });
}

export function useRejectDocument(shipmentId: string) {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      documentId,
      reason,
    }: {
      documentId: string;
      reason: string;
    }) => {
      const res = await fetch(
        `${API_BASE}/api/documents/${documentId}/reject`,
        {
          method: "POST",
          headers: authHeaders(orgId!),
          body: JSON.stringify({ reason }),
        },
      );
      if (!res.ok) throw new Error(`Rejection failed: ${res.status}`);
      return res.json();
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["shipment-documents", orgId, shipmentId],
      });
    },
  });
}

export function useDeleteDocument(shipmentId: string) {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      documentId,
      reason,
    }: {
      documentId: string;
      reason: string;
    }) => {
      const res = await fetch(`${API_BASE}/api/documents/${documentId}`, {
        method: "DELETE",
        headers: authHeaders(orgId!),
        body: JSON.stringify({ reason }),
      });
      if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
      return res.json();
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["shipment-documents", orgId, shipmentId],
      });
    },
  });
}
