"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useCurrentOrg } from "@/lib/auth/org-context";
import type {
  ClassificationResponse,
  ReclassifyResponse,
} from "./classification-types";

export type {
  ClassificationResponse,
  ClassificationAlternative,
  ClassificationInUpload,
  ReclassifyResponse,
  ClassificationMethod,
} from "./classification-types";

export {
  METHOD_LABELS,
  METHOD_COLORS,
  getClassificationConfidenceLevel,
  getClassificationConfidenceColor,
  formatClassificationConfidence,
  getDocTypeLabel,
  isConfidenceActionable,
} from "./classification-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function authHeaders(orgId: string): Record<string, string> {
  return {
    "X-Organization-Id": orgId,
  };
}

// --- Fetch functions ---

async function postClassify(
  orgId: string,
  file: File,
): Promise<ClassificationResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/documents/classify`, {
    method: "POST",
    headers: authHeaders(orgId),
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to classify document");
  return res.json();
}

async function postReclassify(
  orgId: string,
  documentId: string,
): Promise<ReclassifyResponse> {
  const res = await fetch(
    `${API_BASE}/api/documents/${documentId}/reclassify`,
    {
      method: "POST",
      headers: {
        ...authHeaders(orgId),
        "Content-Type": "application/json",
      },
    },
  );
  if (!res.ok) throw new Error("Failed to reclassify document");
  return res.json();
}

// --- React Query Hooks ---

export function useClassifyDocument() {
  const { orgId } = useCurrentOrg();
  return useMutation({
    mutationFn: (file: File) => postClassify(orgId!, file),
  });
}

export function useReclassifyDocument(documentId: string) {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => postReclassify(orgId!, documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["shipment-documents"] });
    },
  });
}
