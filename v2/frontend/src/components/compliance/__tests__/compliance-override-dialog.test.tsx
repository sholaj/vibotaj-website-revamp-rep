import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ComplianceOverrideDialog } from "../compliance-override-dialog";

describe("ComplianceOverrideDialog", () => {
  it("renders dialog title when open", () => {
    render(
      <ComplianceOverrideDialog
        open={true}
        onOpenChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByText("Override Compliance")).toBeInTheDocument();
  });

  it("renders reason textarea", () => {
    render(
      <ComplianceOverrideDialog
        open={true}
        onOpenChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByLabelText("Reason for override")).toBeInTheDocument();
  });

  it("submit button disabled with short reason", async () => {
    const user = userEvent.setup();
    render(
      <ComplianceOverrideDialog
        open={true}
        onOpenChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    const textarea = screen.getByLabelText("Reason for override");
    await user.type(textarea, "Hi");

    const submitBtn = screen.getByRole("button", { name: /Submit Override/i });
    expect(submitBtn).toBeDisabled();
  });

  it("shows validation message for short reason", async () => {
    const user = userEvent.setup();
    render(
      <ComplianceOverrideDialog
        open={true}
        onOpenChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    const textarea = screen.getByLabelText("Reason for override");
    await user.type(textarea, "Hi");

    expect(
      screen.getByText("Reason must be at least 5 characters."),
    ).toBeInTheDocument();
  });

  it("calls onSubmit with reason when valid", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(
      <ComplianceOverrideDialog
        open={true}
        onOpenChange={vi.fn()}
        onSubmit={onSubmit}
      />,
    );

    const textarea = screen.getByLabelText("Reason for override");
    await user.type(textarea, "Valid override reason");

    const submitBtn = screen.getByRole("button", { name: /Submit Override/i });
    expect(submitBtn).not.toBeDisabled();
    await user.click(submitBtn);

    expect(onSubmit).toHaveBeenCalledWith("Valid override reason");
  });

  it("renders cancel button", () => {
    render(
      <ComplianceOverrideDialog
        open={true}
        onOpenChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });

  it("shows Submitting text when isSubmitting", () => {
    render(
      <ComplianceOverrideDialog
        open={true}
        onOpenChange={vi.fn()}
        onSubmit={vi.fn()}
        isSubmitting={true}
      />,
    );
    expect(screen.getByText("Submitting...")).toBeInTheDocument();
  });
});
