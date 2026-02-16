import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { InviteMemberModal } from "../invite-member-modal";

describe("InviteMemberModal", () => {
  it("renders dialog title when open", () => {
    render(
      <InviteMemberModal
        open={true}
        onOpenChange={vi.fn()}
        onInvite={vi.fn()}
      />,
    );
    expect(screen.getByText("Invite Team Member")).toBeInTheDocument();
  });

  it("renders email input", () => {
    render(
      <InviteMemberModal
        open={true}
        onOpenChange={vi.fn()}
        onInvite={vi.fn()}
      />,
    );
    expect(screen.getByPlaceholderText("colleague@company.com")).toBeInTheDocument();
  });

  it("renders role selector", () => {
    render(
      <InviteMemberModal
        open={true}
        onOpenChange={vi.fn()}
        onInvite={vi.fn()}
      />,
    );
    expect(screen.getByText("Role")).toBeInTheDocument();
  });

  it("disables submit with invalid email", () => {
    render(
      <InviteMemberModal
        open={true}
        onOpenChange={vi.fn()}
        onInvite={vi.fn()}
      />,
    );
    expect(screen.getByText("Send Invitation")).toBeDisabled();
  });

  it("enables submit with valid email", async () => {
    const user = userEvent.setup();
    render(
      <InviteMemberModal
        open={true}
        onOpenChange={vi.fn()}
        onInvite={vi.fn()}
      />,
    );
    await user.type(
      screen.getByPlaceholderText("colleague@company.com"),
      "test@example.com",
    );
    expect(screen.getByText("Send Invitation")).toBeEnabled();
  });

  it("shows Sending... when isInviting", async () => {
    const user = userEvent.setup();
    render(
      <InviteMemberModal
        open={true}
        onOpenChange={vi.fn()}
        onInvite={vi.fn()}
        isInviting={true}
      />,
    );
    await user.type(
      screen.getByPlaceholderText("colleague@company.com"),
      "test@example.com",
    );
    expect(screen.getByText("Sending...")).toBeInTheDocument();
  });

  it("calls onInvite with email and default role on submit", async () => {
    const user = userEvent.setup();
    const onInvite = vi.fn();
    render(
      <InviteMemberModal
        open={true}
        onOpenChange={vi.fn()}
        onInvite={onInvite}
      />,
    );
    await user.type(
      screen.getByPlaceholderText("colleague@company.com"),
      "new@example.com",
    );
    await user.click(screen.getByText("Send Invitation"));
    expect(onInvite).toHaveBeenCalledWith("new@example.com", "member");
  });
});
