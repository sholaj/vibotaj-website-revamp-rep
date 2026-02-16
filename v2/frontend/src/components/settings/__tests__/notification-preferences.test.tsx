import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NotificationPreferences } from "../notification-preferences";
import { getDefaultPreferences } from "@/lib/api/notification-types";
import type { NotificationPreference } from "@/lib/api/notification-types";

describe("NotificationPreferences", () => {
  const defaultPrefs = getDefaultPreferences();
  const defaultProps = {
    preferences: defaultPrefs,
    onSave: vi.fn(),
    isSaving: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders category headers", () => {
    render(<NotificationPreferences {...defaultProps} />);
    expect(screen.getByText("Documents")).toBeInTheDocument();
    expect(screen.getByText("Shipments")).toBeInTheDocument();
    expect(screen.getByText("Compliance")).toBeInTheDocument();
    expect(screen.getByText("Team")).toBeInTheDocument();
  });

  it("renders event type labels", () => {
    render(<NotificationPreferences {...defaultProps} />);
    expect(screen.getByText("Document Uploaded")).toBeInTheDocument();
    expect(screen.getByText("Document Approved")).toBeInTheDocument();
    expect(screen.getByText("Document Rejected")).toBeInTheDocument();
    expect(screen.getByText("Shipment Status Change")).toBeInTheDocument();
    expect(screen.getByText("Compliance Alert")).toBeInTheDocument();
    expect(screen.getByText("Document Expiry Warning")).toBeInTheDocument();
    expect(screen.getByText("Invitation Sent")).toBeInTheDocument();
    expect(screen.getByText("Invitation Accepted")).toBeInTheDocument();
  });

  it("renders Email and In-App column headers", () => {
    render(<NotificationPreferences {...defaultProps} />);
    const emailHeaders = screen.getAllByText("Email");
    const inAppHeaders = screen.getAllByText("In-App");
    expect(emailHeaders.length).toBeGreaterThan(0);
    expect(inAppHeaders.length).toBeGreaterThan(0);
  });

  it("renders switches for each preference", () => {
    render(<NotificationPreferences {...defaultProps} />);
    // 8 event types x 2 switches (email + in-app) = 16 switches
    const switches = screen.getAllByRole("switch");
    expect(switches).toHaveLength(16);
  });

  it("all switches are checked by default", () => {
    render(<NotificationPreferences {...defaultProps} />);
    const switches = screen.getAllByRole("switch");
    for (const sw of switches) {
      expect(sw).toHaveAttribute("data-state", "checked");
    }
  });

  it("renders save button disabled initially (no changes)", () => {
    render(<NotificationPreferences {...defaultProps} />);
    const saveBtn = screen.getByRole("button", { name: /Save Preferences/ });
    expect(saveBtn).toBeDisabled();
  });

  it("enables save button after toggling a switch", async () => {
    const user = userEvent.setup();
    render(<NotificationPreferences {...defaultProps} />);
    const switches = screen.getAllByRole("switch");
    const firstSwitch = switches[0]!;
    await user.click(firstSwitch);
    const saveBtn = screen.getByRole("button", { name: /Save Preferences/ });
    expect(saveBtn).not.toBeDisabled();
  });

  it("calls onSave with updated preferences", async () => {
    const user = userEvent.setup();
    render(<NotificationPreferences {...defaultProps} />);
    // Toggle the first email switch (document_uploaded)
    const switches = screen.getAllByRole("switch");
    const firstSwitch = switches[0]!;
    await user.click(firstSwitch);
    // Click save
    await user.click(
      screen.getByRole("button", { name: /Save Preferences/ }),
    );
    expect(defaultProps.onSave).toHaveBeenCalledTimes(1);
    const savedPrefs = defaultProps.onSave.mock
      .calls[0]![0] as NotificationPreference[];
    // The first event should have email_enabled flipped
    const docUploaded = savedPrefs.find(
      (p) => p.event_type === "document_uploaded",
    );
    expect(docUploaded?.email_enabled).toBe(false);
  });

  it("shows saving state", () => {
    render(<NotificationPreferences {...defaultProps} isSaving={true} />);
    expect(screen.getByText("Saving...")).toBeInTheDocument();
  });

  it("renders with some preferences disabled", () => {
    const customPrefs = defaultPrefs.map((p) =>
      p.event_type === "invitation_sent"
        ? { ...p, email_enabled: false }
        : p,
    );
    render(
      <NotificationPreferences {...defaultProps} preferences={customPrefs} />,
    );
    const switches = screen.getAllByRole("switch");
    // invitation_sent email switch should be unchecked
    const invitationEmailSwitch = screen.getByRole("switch", {
      name: /Email for invitation_sent/,
    });
    expect(invitationEmailSwitch).toHaveAttribute("data-state", "unchecked");
  });
});
