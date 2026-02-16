import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AccessDenied } from "../access-denied";

describe("AccessDenied", () => {
  it("renders access denied title", () => {
    render(<AccessDenied />);
    expect(screen.getByText("Access Denied")).toBeInTheDocument();
  });

  it("renders contact admin message", () => {
    render(<AccessDenied />);
    expect(
      screen.getByText(/Contact your organization admin/),
    ).toBeInTheDocument();
  });
});
