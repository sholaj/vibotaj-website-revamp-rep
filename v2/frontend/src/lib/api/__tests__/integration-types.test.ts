import { describe, it, expect } from "vitest";
import {
  INTEGRATION_TYPES,
  INTEGRATION_LABELS,
  INTEGRATION_DESCRIPTIONS,
  CUSTOMS_PROVIDERS,
  BANKING_PROVIDERS,
  METHOD_LABELS,
  STATUS_COLORS,
  STATUS_LABELS,
  getConnectionStatus,
  type IntegrationConfig,
} from "../integration-types";

describe("integration-types", () => {
  describe("INTEGRATION_TYPES", () => {
    it("has 2 integration types", () => {
      expect(INTEGRATION_TYPES).toHaveLength(2);
    });

    it("includes customs and banking", () => {
      expect(INTEGRATION_TYPES).toContain("customs");
      expect(INTEGRATION_TYPES).toContain("banking");
    });
  });

  describe("INTEGRATION_LABELS", () => {
    it("has a label for every type", () => {
      for (const type of INTEGRATION_TYPES) {
        expect(INTEGRATION_LABELS[type]).toBeDefined();
        expect(typeof INTEGRATION_LABELS[type]).toBe("string");
      }
    });

    it("has correct labels", () => {
      expect(INTEGRATION_LABELS.customs).toBe("Customs");
      expect(INTEGRATION_LABELS.banking).toBe("Banking");
    });
  });

  describe("INTEGRATION_DESCRIPTIONS", () => {
    it("has a description for every type", () => {
      for (const type of INTEGRATION_TYPES) {
        expect(INTEGRATION_DESCRIPTIONS[type]).toBeDefined();
        expect(INTEGRATION_DESCRIPTIONS[type].length).toBeGreaterThan(10);
      }
    });
  });

  describe("CUSTOMS_PROVIDERS", () => {
    it("has 3 providers", () => {
      expect(CUSTOMS_PROVIDERS).toHaveLength(3);
    });

    it("includes mock, ncs, and son", () => {
      const values = CUSTOMS_PROVIDERS.map((p) => p.value);
      expect(values).toContain("mock");
      expect(values).toContain("ncs");
      expect(values).toContain("son");
    });
  });

  describe("BANKING_PROVIDERS", () => {
    it("has 3 providers", () => {
      expect(BANKING_PROVIDERS).toHaveLength(3);
    });

    it("includes mock, gtbank, and uba", () => {
      const values = BANKING_PROVIDERS.map((p) => p.value);
      expect(values).toContain("mock");
      expect(values).toContain("gtbank");
      expect(values).toContain("uba");
    });
  });

  describe("METHOD_LABELS", () => {
    it("has labels for key methods", () => {
      expect(METHOD_LABELS.test_connection).toBe("Test Connection");
      expect(METHOD_LABELS.check_pre_clearance).toBe("Pre-Clearance Check");
      expect(METHOD_LABELS.verify_lc).toBe("LC Verification");
      expect(METHOD_LABELS.get_forex_rate).toBe("Forex Rate");
    });
  });

  describe("STATUS_COLORS", () => {
    it("has colors for all statuses", () => {
      expect(STATUS_COLORS.connected).toBeDefined();
      expect(STATUS_COLORS.disconnected).toBeDefined();
      expect(STATUS_COLORS.untested).toBeDefined();
    });
  });

  describe("STATUS_LABELS", () => {
    it("has labels for all statuses", () => {
      expect(STATUS_LABELS.connected).toBe("Connected");
      expect(STATUS_LABELS.disconnected).toBe("Disconnected");
      expect(STATUS_LABELS.untested).toBe("Not Tested");
    });
  });

  describe("getConnectionStatus", () => {
    it("returns untested for null config", () => {
      expect(getConnectionStatus(null)).toBe("untested");
    });

    it("returns connected for successful test", () => {
      const config: IntegrationConfig = {
        id: "1",
        organization_id: "org-1",
        integration_type: "customs",
        provider: "mock",
        is_active: true,
        last_tested_at: "2026-02-16T12:00:00Z",
        last_test_success: true,
        created_at: "2026-02-16T12:00:00Z",
        updated_at: "2026-02-16T12:00:00Z",
      };
      expect(getConnectionStatus(config)).toBe("connected");
    });

    it("returns disconnected for failed test", () => {
      const config: IntegrationConfig = {
        id: "1",
        organization_id: "org-1",
        integration_type: "customs",
        provider: "mock",
        is_active: true,
        last_tested_at: "2026-02-16T12:00:00Z",
        last_test_success: false,
        created_at: "2026-02-16T12:00:00Z",
        updated_at: "2026-02-16T12:00:00Z",
      };
      expect(getConnectionStatus(config)).toBe("disconnected");
    });

    it("returns untested for config with no test result", () => {
      const config: IntegrationConfig = {
        id: "1",
        organization_id: "org-1",
        integration_type: "banking",
        provider: "mock",
        is_active: true,
        last_tested_at: null,
        last_test_success: null,
        created_at: "2026-02-16T12:00:00Z",
        updated_at: "2026-02-16T12:00:00Z",
      };
      expect(getConnectionStatus(config)).toBe("untested");
    });
  });
});
