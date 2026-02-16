import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BolParsedFields } from "../bol-parsed-fields";
import type { BolParsedResponse } from "@/lib/api/bol-types";

const parsedData: BolParsedResponse = {
  document_id: "doc-1",
  parse_status: "parsed",
  parsed_at: "2026-02-16T10:00:00Z",
  confidence_score: 0.85,
  fields: {
    bol_number: { value: "MSC1234567", confidence: 0.95 },
    shipper: { value: "VIBOTAJ Global Nigeria Ltd", confidence: 0.95 },
    consignee: { value: "HAGES GmbH", confidence: 0.95 },
    container_number: { value: "MSCU1234567", confidence: 0.95 },
    vessel_name: { value: "RHINE MAERSK", confidence: 0.80 },
    voyage_number: { value: "550N", confidence: 0.80 },
    port_of_loading: { value: "NGAPP", confidence: 0.80 },
    port_of_discharge: { value: "DEHAM", confidence: 0.80 },
  },
  compliance: {
    decision: "APPROVE",
    rules_passed: 14,
    rules_failed: 1,
    rules_total: 15,
  },
  auto_synced: false,
};

const pendingData: BolParsedResponse = {
  document_id: "doc-2",
  parse_status: "pending",
  parsed_at: null,
  confidence_score: 0,
  fields: {},
  compliance: null,
  auto_synced: false,
};

const failedData: BolParsedResponse = {
  document_id: "doc-3",
  parse_status: "failed",
  parsed_at: null,
  confidence_score: 0,
  fields: {},
  compliance: null,
  auto_synced: false,
};

describe("BolParsedFields", () => {
  it("renders the card", () => {
    render(<BolParsedFields data={parsedData} />);
    expect(screen.getByTestId("bol-parsed-fields")).toBeInTheDocument();
  });

  it("shows Parsed status badge for parsed data", () => {
    render(<BolParsedFields data={parsedData} />);
    expect(screen.getByText("Parsed")).toBeInTheDocument();
  });

  it("shows overall confidence score", () => {
    render(<BolParsedFields data={parsedData} />);
    expect(screen.getByText("85%")).toBeInTheDocument();
  });

  it("renders all field rows", () => {
    render(<BolParsedFields data={parsedData} />);
    expect(screen.getByTestId("bol-field-bol_number")).toBeInTheDocument();
    expect(screen.getByTestId("bol-field-shipper")).toBeInTheDocument();
    expect(screen.getByTestId("bol-field-consignee")).toBeInTheDocument();
    expect(screen.getByTestId("bol-field-container_number")).toBeInTheDocument();
    expect(screen.getByTestId("bol-field-vessel_name")).toBeInTheDocument();
    expect(screen.getByTestId("bol-field-voyage_number")).toBeInTheDocument();
    expect(screen.getByTestId("bol-field-port_of_loading")).toBeInTheDocument();
    expect(screen.getByTestId("bol-field-port_of_discharge")).toBeInTheDocument();
  });

  it("displays field values", () => {
    render(<BolParsedFields data={parsedData} />);
    expect(screen.getByText("MSC1234567")).toBeInTheDocument();
    expect(screen.getByText("VIBOTAJ Global Nigeria Ltd")).toBeInTheDocument();
    expect(screen.getByText("HAGES GmbH")).toBeInTheDocument();
    expect(screen.getByText("RHINE MAERSK")).toBeInTheDocument();
  });

  it("shows compliance summary", () => {
    render(<BolParsedFields data={parsedData} />);
    expect(screen.getByTestId("bol-compliance-summary")).toBeInTheDocument();
    expect(screen.getByText("Approved")).toBeInTheDocument();
    expect(screen.getByText(/14\/15 rules passed/)).toBeInTheDocument();
  });

  it("shows auto-synced badge when auto_synced is true", () => {
    const autoSyncedData = { ...parsedData, auto_synced: true };
    render(<BolParsedFields data={autoSyncedData} />);
    expect(screen.getByText("Auto-synced to shipment")).toBeInTheDocument();
  });

  it("shows pending message for pending status", () => {
    render(<BolParsedFields data={pendingData} />);
    expect(screen.getByText("Pending")).toBeInTheDocument();
    expect(screen.getByText(/Waiting for parse/)).toBeInTheDocument();
  });

  it("shows failed message with retry button", () => {
    const onReparse = vi.fn();
    render(<BolParsedFields data={failedData} onReparse={onReparse} />);
    expect(screen.getByText("Failed")).toBeInTheDocument();
    expect(screen.getByText(/Failed to extract/)).toBeInTheDocument();
    expect(screen.getByText("Try Again")).toBeInTheDocument();
  });

  it("calls onReparse when re-parse button is clicked", async () => {
    const user = userEvent.setup();
    const onReparse = vi.fn();
    render(<BolParsedFields data={parsedData} onReparse={onReparse} />);
    const reparseButton = screen.getByTitle("Re-parse");
    await user.click(reparseButton);
    expect(onReparse).toHaveBeenCalledOnce();
  });

  it("disables re-parse button when reparsing", () => {
    const onReparse = vi.fn();
    render(
      <BolParsedFields data={parsedData} onReparse={onReparse} isReparsing />,
    );
    const reparseButton = screen.getByTitle("Re-parse");
    expect(reparseButton).toBeDisabled();
  });
});
