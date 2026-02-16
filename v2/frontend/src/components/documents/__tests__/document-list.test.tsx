import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DocumentList } from "../document-list";
import type { Document } from "@/lib/api/document-types";

const mockDocs: Document[] = [
  {
    id: "d1",
    shipment_id: "s1",
    document_type: "bill_of_lading",
    status: "approved",
    file_path: "/files/bol.pdf",
    file_name: "bol.pdf",
    file_size: 1024,
    reference_number: "BL-001",
    issue_date: "2026-02-01T00:00:00Z",
    expiry_date: null,
    issuer: null,
    notes: null,
    uploaded_by: "user-1",
    reviewed_by: "user-2",
    created_at: "2026-02-01T00:00:00Z",
    updated_at: "2026-02-01T00:00:00Z",
  },
  {
    id: "d2",
    shipment_id: "s1",
    document_type: "commercial_invoice",
    status: "uploaded",
    file_path: null,
    file_name: null,
    file_size: null,
    reference_number: null,
    issue_date: null,
    expiry_date: null,
    issuer: null,
    notes: null,
    uploaded_by: "user-1",
    reviewed_by: null,
    created_at: "2026-02-02T00:00:00Z",
    updated_at: "2026-02-02T00:00:00Z",
  },
];

describe("DocumentList", () => {
  const defaultProps = {
    documents: mockDocs,
    missingTypes: ["packing_list" as const, "certificate_of_origin" as const],
    onUpload: vi.fn(),
    onSelect: vi.fn(),
    onDownload: vi.fn(),
  };

  it("renders document type labels", () => {
    render(<DocumentList {...defaultProps} />);
    expect(screen.getByText("Bill of Lading")).toBeInTheDocument();
    expect(screen.getByText("Commercial Invoice")).toBeInTheDocument();
  });

  it("renders document count in header", () => {
    render(<DocumentList {...defaultProps} />);
    expect(screen.getByText("Documents (2)")).toBeInTheDocument();
  });

  it("renders reference numbers", () => {
    render(<DocumentList {...defaultProps} />);
    expect(screen.getByText("BL-001")).toBeInTheDocument();
  });

  it("calls onUpload when Upload button clicked", async () => {
    const user = userEvent.setup();
    render(<DocumentList {...defaultProps} />);
    await user.click(screen.getByText("Upload"));
    expect(defaultProps.onUpload).toHaveBeenCalled();
  });

  it("calls onSelect when document row clicked", async () => {
    const user = userEvent.setup();
    render(<DocumentList {...defaultProps} />);
    await user.click(screen.getByText("Bill of Lading"));
    expect(defaultProps.onSelect).toHaveBeenCalledWith(mockDocs[0]);
  });

  it("renders missing documents section", () => {
    render(<DocumentList {...defaultProps} />);
    expect(screen.getByText("Missing Documents (2)")).toBeInTheDocument();
    expect(screen.getByText("Packing List")).toBeInTheDocument();
    expect(screen.getByText("Certificate of Origin")).toBeInTheDocument();
  });

  it("hides missing section when no missing types", () => {
    render(<DocumentList {...defaultProps} missingTypes={[]} />);
    expect(screen.queryByText(/Missing Documents/)).not.toBeInTheDocument();
  });

  it("renders empty state when no documents", () => {
    render(<DocumentList {...defaultProps} documents={[]} />);
    expect(screen.getByText("No documents uploaded yet")).toBeInTheDocument();
  });
});
