import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DocumentReviewPanel } from "../document-review-panel";
import type { Document } from "@/lib/api/document-types";

// --- Mocks ---

const mockReclassifyMutate = vi.fn();
let mockReclassifyState: {
  isPending: boolean;
  isSuccess: boolean;
  data: {
    document_id: string;
    previous_type: string;
    new_type: string;
    auto_applied: boolean;
  } | null;
  mutate: typeof mockReclassifyMutate;
};

vi.mock("@/lib/api/classification", () => ({
  useReclassifyDocument: () => mockReclassifyState,
}));

vi.mock("@/lib/auth/org-context", () => ({
  useCurrentOrg: () => ({ orgId: "org-1" }),
}));

const mockDoc: Document = {
  id: "doc-1",
  shipment_id: "s1",
  document_type: "bill_of_lading",
  status: "uploaded",
  file_path: "/files/bol.pdf",
  file_name: "bol.pdf",
  file_size: 2048,
  reference_number: "BL-001",
  issue_date: "2026-02-01T00:00:00Z",
  expiry_date: null,
  issuer: "Carrier Lines Ltd",
  notes: "Pending verification",
  uploaded_by: "user-1",
  reviewed_by: null,
  created_at: "2026-02-01T00:00:00Z",
  updated_at: "2026-02-01T00:00:00Z",
};

const approvedDoc: Document = {
  ...mockDoc,
  id: "doc-2",
  status: "approved",
  reviewed_by: "user-2",
};

describe("DocumentReviewPanel", () => {
  const defaultProps = {
    document: mockDoc,
    open: true,
    onOpenChange: vi.fn(),
    onApprove: vi.fn(),
    onReject: vi.fn(),
    onDelete: vi.fn(),
    onDownload: vi.fn(),
    canApprove: true,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockReclassifyState = {
      isPending: false,
      isSuccess: false,
      data: null,
      mutate: mockReclassifyMutate,
    };
  });

  it("renders document title", () => {
    render(<DocumentReviewPanel {...defaultProps} />);
    expect(screen.getByText("Bill of Lading")).toBeInTheDocument();
  });

  it("renders document details", () => {
    render(<DocumentReviewPanel {...defaultProps} />);
    expect(screen.getByText("BL-001")).toBeInTheDocument();
    expect(screen.getByText("bol.pdf")).toBeInTheDocument();
    expect(screen.getByText("Carrier Lines Ltd")).toBeInTheDocument();
  });

  it("renders reclassify button for uploaded documents", () => {
    render(<DocumentReviewPanel {...defaultProps} />);
    expect(
      screen.getByRole("button", { name: /Re-classify with AI/ }),
    ).toBeInTheDocument();
  });

  it("does not render reclassify button for approved documents", () => {
    render(<DocumentReviewPanel {...defaultProps} document={approvedDoc} />);
    expect(
      screen.queryByRole("button", { name: /Re-classify/ }),
    ).not.toBeInTheDocument();
  });

  it("calls reclassify mutation on button click", async () => {
    const user = userEvent.setup();
    render(<DocumentReviewPanel {...defaultProps} />);
    await user.click(
      screen.getByRole("button", { name: /Re-classify with AI/ }),
    );
    expect(mockReclassifyMutate).toHaveBeenCalled();
  });

  it("shows loading state during reclassification", () => {
    mockReclassifyState.isPending = true;
    render(<DocumentReviewPanel {...defaultProps} />);
    expect(screen.getByText("Reclassifying...")).toBeInTheDocument();
  });

  it("shows reclassification result on success", () => {
    mockReclassifyState.isSuccess = true;
    mockReclassifyState.data = {
      document_id: "doc-1",
      previous_type: "other",
      new_type: "bill_of_lading",
      auto_applied: true,
    };
    render(<DocumentReviewPanel {...defaultProps} />);
    expect(screen.getByText("Reclassification Result")).toBeInTheDocument();
    expect(screen.getByText(/Other/)).toBeInTheDocument();
    expect(screen.getByText(/auto-applied/)).toBeInTheDocument();
  });

  it("renders classification method badge when provided", () => {
    render(
      <DocumentReviewPanel
        {...defaultProps}
        classificationMethod="ai"
        classificationConfidence={0.92}
      />,
    );
    expect(screen.getByText("AI Detected")).toBeInTheDocument();
    expect(screen.getByText("92%")).toBeInTheDocument();
  });

  it("renders keyword method badge", () => {
    render(
      <DocumentReviewPanel
        {...defaultProps}
        classificationMethod="keyword"
        classificationConfidence={0.65}
      />,
    );
    expect(screen.getByText("Keyword Match")).toBeInTheDocument();
    expect(screen.getByText("65%")).toBeInTheDocument();
  });

  it("does not show classification info when no method provided", () => {
    render(<DocumentReviewPanel {...defaultProps} />);
    expect(screen.queryByText("Classification")).not.toBeInTheDocument();
  });

  it("returns null when document is null", () => {
    const { container } = render(
      <DocumentReviewPanel {...defaultProps} document={null} />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders Download button when file_path exists", () => {
    render(<DocumentReviewPanel {...defaultProps} />);
    expect(
      screen.getByRole("button", { name: /Download/ }),
    ).toBeInTheDocument();
  });

  it("calls onDownload when Download clicked", async () => {
    const user = userEvent.setup();
    render(<DocumentReviewPanel {...defaultProps} />);
    await user.click(screen.getByRole("button", { name: /Download/ }));
    expect(defaultProps.onDownload).toHaveBeenCalledWith(mockDoc);
  });

  it("renders review section when canApprove and status is uploaded", () => {
    render(<DocumentReviewPanel {...defaultProps} />);
    expect(screen.getByText("Review")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Approve/ }),
    ).toBeInTheDocument();
  });

  it("hides review section when canApprove is false", () => {
    render(
      <DocumentReviewPanel {...defaultProps} canApprove={false} />,
    );
    expect(screen.queryByText("Review")).not.toBeInTheDocument();
  });

  it("renders notes when present", () => {
    render(<DocumentReviewPanel {...defaultProps} />);
    expect(screen.getByText("Pending verification")).toBeInTheDocument();
  });

  it("renders under_review documents with reclassify button", () => {
    const underReviewDoc = { ...mockDoc, status: "under_review" as const };
    render(
      <DocumentReviewPanel {...defaultProps} document={underReviewDoc} />,
    );
    expect(
      screen.getByRole("button", { name: /Re-classify with AI/ }),
    ).toBeInTheDocument();
  });
});
