import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuditPackCard } from "../audit-pack-card";
import type { AuditPackContent } from "@/lib/api/audit-pack-types";

const mockContents: AuditPackContent[] = [
  { name: "00-SHIPMENT-INDEX.pdf", type: "index" },
  { name: "01-bill_of_lading.pdf", type: "document", document_type: "bill_of_lading" },
  { name: "02-certificate_of_origin.pdf", type: "document", document_type: "certificate_of_origin" },
  { name: "container-tracking-log.json", type: "tracking" },
  { name: "metadata.json", type: "metadata" },
];

describe("AuditPackCard", () => {
  it("renders the card", () => {
    render(
      <AuditPackCard
        status="ready"
        generatedAt="2026-02-16T10:00:00Z"
        documentCount={5}
        contents={mockContents}
        isOutdated={false}
        complianceDecision="APPROVE"
      />,
    );
    expect(screen.getByTestId("audit-pack-card")).toBeInTheDocument();
  });

  it("shows Ready status badge", () => {
    render(
      <AuditPackCard
        status="ready"
        generatedAt="2026-02-16T10:00:00Z"
        documentCount={5}
        contents={mockContents}
        isOutdated={false}
        complianceDecision="APPROVE"
      />,
    );
    expect(screen.getByTestId("pack-status-badge")).toHaveTextContent("Ready");
  });

  it("shows Not Generated for none status", () => {
    render(
      <AuditPackCard
        status="none"
        generatedAt={null}
        documentCount={0}
        contents={[]}
        isOutdated={true}
        complianceDecision={null}
      />,
    );
    expect(screen.getByTestId("pack-status-badge")).toHaveTextContent("Not Generated");
  });

  it("shows Outdated status badge", () => {
    render(
      <AuditPackCard
        status="outdated"
        generatedAt="2026-02-15T10:00:00Z"
        documentCount={3}
        contents={mockContents}
        isOutdated={true}
        complianceDecision="HOLD"
      />,
    );
    expect(screen.getByTestId("pack-status-badge")).toHaveTextContent("Outdated");
  });

  it("shows document count", () => {
    render(
      <AuditPackCard
        status="ready"
        generatedAt="2026-02-16T10:00:00Z"
        documentCount={5}
        contents={mockContents}
        isOutdated={false}
        complianceDecision="APPROVE"
      />,
    );
    expect(screen.getByTestId("document-count")).toHaveTextContent("5");
  });

  it("shows compliance decision", () => {
    render(
      <AuditPackCard
        status="ready"
        generatedAt="2026-02-16T10:00:00Z"
        documentCount={5}
        contents={mockContents}
        isOutdated={false}
        complianceDecision="APPROVE"
      />,
    );
    expect(screen.getByTestId("compliance-decision")).toHaveTextContent("APPROVE");
  });

  it("shows generated at timestamp", () => {
    render(
      <AuditPackCard
        status="ready"
        generatedAt="2026-02-16T10:00:00Z"
        documentCount={5}
        contents={mockContents}
        isOutdated={false}
        complianceDecision="APPROVE"
      />,
    );
    const genAt = screen.getByTestId("generated-at");
    expect(genAt.textContent).not.toBe("Never");
  });

  it("shows Never when no generated date", () => {
    render(
      <AuditPackCard
        status="none"
        generatedAt={null}
        documentCount={0}
        contents={[]}
        isOutdated={true}
        complianceDecision={null}
      />,
    );
    expect(screen.getByTestId("generated-at")).toHaveTextContent("Never");
  });

  it("shows outdated warning when outdated and not none", () => {
    render(
      <AuditPackCard
        status="outdated"
        generatedAt="2026-02-15T10:00:00Z"
        documentCount={3}
        contents={mockContents}
        isOutdated={true}
        complianceDecision="HOLD"
      />,
    );
    expect(screen.getByTestId("outdated-warning")).toBeInTheDocument();
  });

  it("does not show outdated warning when status is none", () => {
    render(
      <AuditPackCard
        status="none"
        generatedAt={null}
        documentCount={0}
        contents={[]}
        isOutdated={true}
        complianceDecision={null}
      />,
    );
    expect(screen.queryByTestId("outdated-warning")).not.toBeInTheDocument();
  });

  it("renders contents list", () => {
    render(
      <AuditPackCard
        status="ready"
        generatedAt="2026-02-16T10:00:00Z"
        documentCount={5}
        contents={mockContents}
        isOutdated={false}
        complianceDecision="APPROVE"
      />,
    );
    const list = screen.getByTestId("contents-list");
    expect(list.children).toHaveLength(5);
  });

  it("shows download button", () => {
    render(
      <AuditPackCard
        status="ready"
        generatedAt="2026-02-16T10:00:00Z"
        documentCount={5}
        contents={mockContents}
        isOutdated={false}
        complianceDecision="APPROVE"
      />,
    );
    expect(screen.getByTestId("download-btn")).toBeInTheDocument();
  });

  it("calls onDownload when download button clicked", async () => {
    const user = userEvent.setup();
    const onDownload = vi.fn();
    render(
      <AuditPackCard
        status="ready"
        generatedAt="2026-02-16T10:00:00Z"
        documentCount={5}
        contents={mockContents}
        isOutdated={false}
        complianceDecision="APPROVE"
        onDownload={onDownload}
      />,
    );
    await user.click(screen.getByTestId("download-btn"));
    expect(onDownload).toHaveBeenCalledOnce();
  });

  it("shows regenerate button when outdated", () => {
    render(
      <AuditPackCard
        status="outdated"
        generatedAt="2026-02-15T10:00:00Z"
        documentCount={3}
        contents={mockContents}
        isOutdated={true}
        complianceDecision="HOLD"
      />,
    );
    expect(screen.getByTestId("regenerate-btn")).toBeInTheDocument();
  });

  it("shows regenerate button when status is none", () => {
    render(
      <AuditPackCard
        status="none"
        generatedAt={null}
        documentCount={0}
        contents={[]}
        isOutdated={true}
        complianceDecision={null}
      />,
    );
    expect(screen.getByTestId("regenerate-btn")).toBeInTheDocument();
  });

  it("does not show regenerate button when ready and not outdated", () => {
    render(
      <AuditPackCard
        status="ready"
        generatedAt="2026-02-16T10:00:00Z"
        documentCount={5}
        contents={mockContents}
        isOutdated={false}
        complianceDecision="APPROVE"
      />,
    );
    expect(screen.queryByTestId("regenerate-btn")).not.toBeInTheDocument();
  });

  it("calls onRegenerate when regenerate button clicked", async () => {
    const user = userEvent.setup();
    const onRegenerate = vi.fn();
    render(
      <AuditPackCard
        status="outdated"
        generatedAt="2026-02-15T10:00:00Z"
        documentCount={3}
        contents={mockContents}
        isOutdated={true}
        complianceDecision="HOLD"
        onRegenerate={onRegenerate}
      />,
    );
    await user.click(screen.getByTestId("regenerate-btn"));
    expect(onRegenerate).toHaveBeenCalledOnce();
  });

  it("disables buttons when downloading", () => {
    render(
      <AuditPackCard
        status="outdated"
        generatedAt="2026-02-15T10:00:00Z"
        documentCount={3}
        contents={mockContents}
        isOutdated={true}
        complianceDecision="HOLD"
        isDownloading={true}
      />,
    );
    expect(screen.getByTestId("download-btn")).toBeDisabled();
    expect(screen.getByTestId("regenerate-btn")).toBeDisabled();
  });

  it("shows Generating... text when downloading", () => {
    render(
      <AuditPackCard
        status="ready"
        generatedAt="2026-02-16T10:00:00Z"
        documentCount={5}
        contents={mockContents}
        isOutdated={false}
        complianceDecision="APPROVE"
        isDownloading={true}
      />,
    );
    expect(screen.getByTestId("download-btn")).toHaveTextContent("Generating...");
  });
});
