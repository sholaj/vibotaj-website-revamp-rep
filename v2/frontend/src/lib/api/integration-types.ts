/**
 * Types and constants for third-party integrations (PRD-021).
 *
 * Pure types — no API calls, no React hooks.
 */

// --- Integration types ---

export type IntegrationType = "customs" | "banking";

export const INTEGRATION_TYPES: IntegrationType[] = ["customs", "banking"];

export const INTEGRATION_LABELS: Record<IntegrationType, string> = {
  customs: "Customs",
  banking: "Banking",
};

export const INTEGRATION_DESCRIPTIONS: Record<IntegrationType, string> = {
  customs:
    "Pre-clearance checks, duty calculations, and export declaration submission via NCS/SON.",
  banking:
    "Letter of Credit verification, payment status tracking, and forex rate lookups.",
};

// --- Providers ---

export type CustomsProvider = "ncs" | "son" | "mock";
export type BankingProvider = "gtbank" | "uba" | "mock";

export const CUSTOMS_PROVIDERS: { value: CustomsProvider; label: string }[] = [
  { value: "mock", label: "Mock (Development)" },
  { value: "ncs", label: "Nigeria Customs Service" },
  { value: "son", label: "Standards Organisation of Nigeria" },
];

export const BANKING_PROVIDERS: { value: BankingProvider; label: string }[] = [
  { value: "mock", label: "Mock (Development)" },
  { value: "gtbank", label: "Guaranty Trust Bank" },
  { value: "uba", label: "United Bank for Africa" },
];

// --- API response types ---

export interface IntegrationConfig {
  id: string;
  organization_id: string;
  integration_type: IntegrationType;
  provider: string;
  is_active: boolean;
  last_tested_at: string | null;
  last_test_success: boolean | null;
  created_at: string;
  updated_at: string;
}

export interface IntegrationsListResponse {
  customs: IntegrationConfig | null;
  banking: IntegrationConfig | null;
}

export interface IntegrationConfigUpdate {
  provider: string;
  config: Record<string, unknown>;
  is_active: boolean;
}

export interface TestConnectionResponse {
  integration_type: string;
  provider: string;
  success: boolean;
  message: string;
  response_time_ms: number | null;
}

export interface IntegrationLog {
  id: string;
  integration_type: string;
  provider: string;
  method: string;
  request_summary: string | null;
  status: string;
  response_time_ms: number | null;
  error_message: string | null;
  shipment_id: string | null;
  created_at: string;
}

export interface IntegrationLogsResponse {
  logs: IntegrationLog[];
  total: number;
}

// --- Status helpers ---

export type ConnectionStatus = "connected" | "disconnected" | "untested";

export function getConnectionStatus(
  config: IntegrationConfig | null,
): ConnectionStatus {
  if (!config) return "untested";
  if (config.last_test_success === true) return "connected";
  if (config.last_test_success === false) return "disconnected";
  return "untested";
}

export const STATUS_COLORS: Record<ConnectionStatus, string> = {
  connected: "bg-green-500",
  disconnected: "bg-red-500",
  untested: "bg-gray-400",
};

export const STATUS_LABELS: Record<ConnectionStatus, string> = {
  connected: "Connected",
  disconnected: "Disconnected",
  untested: "Not Tested",
};

// --- Method labels for log display ---

export const METHOD_LABELS: Record<string, string> = {
  test_connection: "Test Connection",
  check_pre_clearance: "Pre-Clearance Check",
  calculate_duty: "Duty Calculation",
  submit_declaration: "Submit Declaration",
  get_declaration_status: "Declaration Status",
  verify_lc: "LC Verification",
  get_payment_status: "Payment Status",
  get_forex_rate: "Forex Rate",
};
