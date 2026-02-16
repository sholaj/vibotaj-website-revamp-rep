// --- Notification preference types (no React/PropelAuth dependencies) ---
// PRD-020: Email Notifications

/** Supported notification event types */
export type NotificationEventType =
  | "document_uploaded"
  | "document_validated"
  | "document_rejected"
  | "shipment_status_change"
  | "compliance_alert"
  | "expiry_warning"
  | "invitation_sent"
  | "invitation_accepted";

/** Single event preference */
export interface NotificationPreference {
  event_type: NotificationEventType;
  email_enabled: boolean;
  in_app_enabled: boolean;
}

/** Full preferences response */
export interface NotificationPreferencesResponse {
  preferences: NotificationPreference[];
}

/** Update request (partial — only listed events are updated) */
export interface NotificationPreferencesUpdate {
  preferences: NotificationPreference[];
}

/** Email system status */
export interface EmailStatusResponse {
  enabled: boolean;
  provider: string;
  available: boolean;
}

// --- Constants ---

/** All configurable notification event types */
export const ALL_EVENT_TYPES: NotificationEventType[] = [
  "document_uploaded",
  "document_validated",
  "document_rejected",
  "shipment_status_change",
  "compliance_alert",
  "expiry_warning",
  "invitation_sent",
  "invitation_accepted",
];

/** Human-readable labels for event types */
export const EVENT_TYPE_LABELS: Record<NotificationEventType, string> = {
  document_uploaded: "Document Uploaded",
  document_validated: "Document Approved",
  document_rejected: "Document Rejected",
  shipment_status_change: "Shipment Status Change",
  compliance_alert: "Compliance Alert",
  expiry_warning: "Document Expiry Warning",
  invitation_sent: "Invitation Sent",
  invitation_accepted: "Invitation Accepted",
};

/** Category grouping for UI display */
export type NotificationCategory = "documents" | "shipments" | "compliance" | "team";

export const EVENT_CATEGORIES: Record<NotificationEventType, NotificationCategory> = {
  document_uploaded: "documents",
  document_validated: "documents",
  document_rejected: "documents",
  shipment_status_change: "shipments",
  compliance_alert: "compliance",
  expiry_warning: "compliance",
  invitation_sent: "team",
  invitation_accepted: "team",
};

export const CATEGORY_LABELS: Record<NotificationCategory, string> = {
  documents: "Documents",
  shipments: "Shipments",
  compliance: "Compliance",
  team: "Team",
};

/** Group event types by category */
export function groupByCategory(
  events: NotificationEventType[],
): Record<NotificationCategory, NotificationEventType[]> {
  const groups: Record<NotificationCategory, NotificationEventType[]> = {
    documents: [],
    shipments: [],
    compliance: [],
    team: [],
  };
  for (const et of events) {
    groups[EVENT_CATEGORIES[et]].push(et);
  }
  return groups;
}

/** Get default preferences (all enabled) */
export function getDefaultPreferences(): NotificationPreference[] {
  return ALL_EVENT_TYPES.map((et) => ({
    event_type: et,
    email_enabled: true,
    in_app_enabled: true,
  }));
}
