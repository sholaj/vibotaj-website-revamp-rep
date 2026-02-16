import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BolSyncPreview } from "../bol-sync-preview";
import type {
  BolSyncPreviewResponse,
  CrossValidationIssue,
} from "@/lib/api/bol-types";

const previewWithChanges: BolSyncPreviewResponse = {
  document_id: "doc-1",
  shipment_id: "ship-1",
  shipment_reference: "VIBO-2026-001",
  changes: [
    {
      field: "bl_number",
      current: null,
      new_value: "MSC1234567",
      is_placeholder: false,
      will_update: true,
    },
    {
      field: "container_number",
      current: "HAGES-CNT-001",
      new_value: "MSCU1234567",
      is_placeholder: true,
      will_update: true,
    },
    {
      field: "vessel_name",
      current: null,
      new_value: "RHINE MAERSK",
      is_placeholder: false,
      will_update: true,
    },
    {
      field: "voyage_number",
      current: "550N",
      new_value: "550N",
      is_placeholder: false,
      will_update: false,
    },
  ],
  auto_synced: false,
};

const emptyPreview: BolSyncPreviewResponse = {
  document_id: "doc-2",
  shipment_id: "",
  shipment_reference: "",
  changes: [],
  auto_synced: false,
};

const crossValidationIssues: CrossValidationIssue[] = [
  {
    rule_id: "CROSS-001",
    rule_name: "BoL vs Packing List Weight",
    passed: false,
    severity: "WARNING",
    message: "BoL gross weight (25,000.00 kg) differs from Packing List (20,000.00 kg) by 20.0%",
  },
];

describe("BolSyncPreview", () => {
  it("renders the card", () => {
    render(<BolSyncPreview preview={previewWithChanges} />);
    expect(screen.getByTestId("bol-sync-preview")).toBeInTheDocument();
  });

  it("shows shipment reference", () => {
    render(<BolSyncPreview preview={previewWithChanges} />);
    expect(screen.getByText(/VIBO-2026-001/)).toBeInTheDocument();
  });

  it("shows update count badge", () => {
    render(<BolSyncPreview preview={previewWithChanges} />);
    expect(screen.getByText("3 updates")).toBeInTheDocument();
  });

  it("renders change rows", () => {
    render(<BolSyncPreview preview={previewWithChanges} />);
    expect(screen.getByTestId("sync-change-bl_number")).toBeInTheDocument();
    expect(screen.getByTestId("sync-change-container_number")).toBeInTheDocument();
    expect(screen.getByTestId("sync-change-vessel_name")).toBeInTheDocument();
    expect(screen.getByTestId("sync-change-voyage_number")).toBeInTheDocument();
  });

  it("shows new values", () => {
    render(<BolSyncPreview preview={previewWithChanges} />);
    expect(screen.getByText("MSC1234567")).toBeInTheDocument();
    expect(screen.getByText("MSCU1234567")).toBeInTheDocument();
    expect(screen.getByText("RHINE MAERSK")).toBeInTheDocument();
  });

  it("shows placeholder badge for placeholder changes", () => {
    render(<BolSyncPreview preview={previewWithChanges} />);
    expect(screen.getByText("Placeholder")).toBeInTheDocument();
  });

  it("shows Will update badges", () => {
    render(<BolSyncPreview preview={previewWithChanges} />);
    const badges = screen.getAllByText("Will update");
    expect(badges.length).toBe(3);
  });

  it("shows no changes message for empty preview", () => {
    render(<BolSyncPreview preview={emptyPreview} />);
    expect(screen.getByText("No changes to sync")).toBeInTheDocument();
  });

  it("shows apply button with update count", () => {
    const onApply = vi.fn();
    render(
      <BolSyncPreview preview={previewWithChanges} onApplySync={onApply} />,
    );
    expect(screen.getByText("Apply 3 Updates")).toBeInTheDocument();
  });

  it("calls onApplySync when button is clicked", async () => {
    const user = userEvent.setup();
    const onApply = vi.fn();
    render(
      <BolSyncPreview preview={previewWithChanges} onApplySync={onApply} />,
    );
    await user.click(screen.getByText("Apply 3 Updates"));
    expect(onApply).toHaveBeenCalledOnce();
  });

  it("shows syncing state", () => {
    render(
      <BolSyncPreview
        preview={previewWithChanges}
        onApplySync={vi.fn()}
        isSyncing
      />,
    );
    expect(screen.getByText("Syncing...")).toBeInTheDocument();
  });

  it("shows success state after sync", () => {
    render(
      <BolSyncPreview
        preview={previewWithChanges}
        onApplySync={vi.fn()}
        syncSuccess
      />,
    );
    expect(screen.getByText("Sync applied successfully")).toBeInTheDocument();
  });

  it("hides apply button when auto_synced", () => {
    const autoSyncedPreview = { ...previewWithChanges, auto_synced: true };
    render(
      <BolSyncPreview
        preview={autoSyncedPreview}
        onApplySync={vi.fn()}
      />,
    );
    expect(screen.queryByText(/Apply/)).not.toBeInTheDocument();
    expect(screen.getByText(/auto-synced/)).toBeInTheDocument();
  });

  it("shows cross-validation issues", () => {
    render(
      <BolSyncPreview
        preview={previewWithChanges}
        crossValidation={crossValidationIssues}
      />,
    );
    expect(screen.getByText("Cross-Document Validation")).toBeInTheDocument();
    expect(
      screen.getByTestId("validation-issue-CROSS-001"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("BoL vs Packing List Weight"),
    ).toBeInTheDocument();
  });

  it("shows placeholder count text", () => {
    render(<BolSyncPreview preview={previewWithChanges} />);
    expect(screen.getByText(/1 placeholder/)).toBeInTheDocument();
  });
});
