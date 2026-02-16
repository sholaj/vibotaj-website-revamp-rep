import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  StatusBadge,
  type ShipmentStatus,
  type DocumentStatus,
  type Role,
} from "../status-badge";

describe("StatusBadge", () => {
  describe("shipment variant", () => {
    const statuses: ShipmentStatus[] = [
      "draft",
      "docs_pending",
      "docs_complete",
      "in_transit",
      "arrived",
      "customs",
      "delivered",
      "archived",
    ];

    it.each(statuses)("renders shipment status: %s", (status) => {
      render(<StatusBadge variant="shipment" status={status} />);
      const badge = screen.getByText(
        /draft|docs pending|docs complete|in transit|arrived|at customs|delivered|archived/i,
      );
      expect(badge).toBeInTheDocument();
    });

    it("renders correct label for docs_pending", () => {
      render(<StatusBadge variant="shipment" status="docs_pending" />);
      expect(screen.getByText("Docs Pending")).toBeInTheDocument();
    });

    it("renders correct label for in_transit", () => {
      render(<StatusBadge variant="shipment" status="in_transit" />);
      expect(screen.getByText("In Transit")).toBeInTheDocument();
    });
  });

  describe("document variant", () => {
    const statuses: DocumentStatus[] = [
      "pending",
      "uploaded",
      "under_review",
      "approved",
      "rejected",
      "expired",
    ];

    it.each(statuses)("renders document status: %s", (status) => {
      render(<StatusBadge variant="document" status={status} />);
      const badge = screen.getByText(
        /pending|uploaded|under review|approved|rejected|expired/i,
      );
      expect(badge).toBeInTheDocument();
    });

    it("renders correct label for under_review", () => {
      render(<StatusBadge variant="document" status="under_review" />);
      expect(screen.getByText("Under Review")).toBeInTheDocument();
    });
  });

  describe("role variant", () => {
    const roles: Role[] = [
      "admin",
      "compliance_officer",
      "logistics",
      "buyer",
      "supplier",
      "viewer",
    ];

    it.each(roles)("renders role badge: %s", (role) => {
      render(<StatusBadge variant="role" status={role} />);
      const badge = screen.getByText(
        /admin|compliance|logistics|buyer|supplier|viewer/i,
      );
      expect(badge).toBeInTheDocument();
    });

    it("renders compliance_officer as 'Compliance'", () => {
      render(<StatusBadge variant="role" status="compliance_officer" />);
      expect(screen.getByText("Compliance")).toBeInTheDocument();
    });
  });
});
